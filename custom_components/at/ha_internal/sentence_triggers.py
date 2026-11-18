"""
Sentence triggers on Home Assistant's built-in conversation agent.

Uses ``AgentManager.register_trigger`` (docs/development/SPIKE-FINDINGS.md item 1). That API
treats every ``{slot}`` as a wildcard, so the range and value lists the sentences need are
added to the data block ``register_trigger`` just stored (a private dict shape, see
``_inject_lists``). If that shape is ever not found, the sentences are registered again with
each list spelled out as literal alternatives, which needs only the public call.

Either way Home Assistant's match is only a gate: the sentence is parsed again with ``at``'s
own hassil intents (real lists, one intent per group) and ``recognize_best`` picks the group
and the parse with the most literal text. That is what keeps one group from shadowing another
("cancel the job at 6" is a cancel, not "schedule 'cancel the job' at 6") and an optional
time word from leaking into a wildcard.
"""

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
import re
from typing import TYPE_CHECKING, Any

from hassil import Intents, recognize_best

from custom_components.at.const import LOGGER
from homeassistant.components.conversation.agent_manager import get_agent_manager
from homeassistant.components.conversation.const import IntentSource

if TYPE_CHECKING:
    from hassil.recognize import RecognizeResult

    from homeassistant.components.conversation import ConversationInput
    from homeassistant.components.conversation.agent_manager import AgentManager
    from homeassistant.core import Context, HomeAssistant

_LIST_REFERENCE = re.compile(r"\{([^{}:]+)(?::[^{}]*)?\}")
_GROUP_PREFIX = "AtGroup"


@dataclass
class TriggerInput:
    """A sentence that matched one group, with its slot values."""

    sentence: str
    wildcards: dict[str, str]
    language: str
    device_id: str | None
    satellite_id: str | None
    context: Context
    agent_id: str | None = None
    conversation_id: str | None = None
    spans: dict[str, tuple[int, int]] = field(default_factory=dict)

    def sentence_without(self, name: str) -> str:
        """Return the sentence with one slot's text cut out, trimmed."""
        start, end = self.spans[name]
        return f"{self.sentence[:start].strip()} {self.sentence[end:].strip()}".strip()


TriggerCallback = Callable[[TriggerInput], Awaitable[str]]


@dataclass(frozen=True)
class SentenceGroup:
    """Sentence templates that share one callback."""

    sentences: list[str]
    callback: TriggerCallback


def _wildcard_names(groups: Sequence[SentenceGroup], lists: Mapping[str, Any]) -> set[str]:
    return {
        name
        for group in groups
        for sentence in group.sentences
        for name in _LIST_REFERENCE.findall(sentence)
        if name not in lists
    }


def _value_text(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _list_alternatives(spec: Mapping[str, Any]) -> str:
    """Spell a hassil list out as ``(a|b|c)`` for the public-only registration."""
    if "range" in spec:
        bounds = spec["range"]
        words = range(bounds["from"], bounds["to"] + 1, bounds.get("step", 1))
        return "(" + "|".join(str(number) for number in words) + ")"
    values = [value["in"] if isinstance(value, Mapping) else value for value in spec["values"]]
    return "(" + "|".join(values) + ")"


def _spell_out_lists(sentences: list[str], lists: Mapping[str, Any]) -> list[str]:
    alternatives = {name: _list_alternatives(spec) for name, spec in lists.items()}

    def replace(match: re.Match[str]) -> str:
        return alternatives.get(match.group(1), match.group(0))

    # A list reference matches "6am" as well as "6 am"; literal text needs the space made optional.
    return [_LIST_REFERENCE.sub(replace, sentence).replace(" [", "[ ][") for sentence in sentences]


def _inject_lists(manager: AgentManager, sentences: list[str], lists: Mapping[str, Any]) -> bool:
    """
    Give a just-registered trigger real slot lists (private contract, spike item 1).

    ``register_trigger`` stores ``{"data": [{"sentences": sentences}]}`` under
    ``IntentSource.TRIGGER``, ``subscribe_intents`` hands out the live dict, and the default
    agent rebuilds its trigger intents lazily. Data-level lists beat the wildcards it assumes.
    This must run right after ``register_trigger``, with no ``await`` in between.

    Returns:
        True when the lists were added, False when the stored trigger was not found.

    """
    live: dict[Any, Any] = {}
    manager.subscribe_intents(live.update)()
    try:
        blocks = [
            data
            for trigger_intent in live[IntentSource.TRIGGER]["intents"].values()
            for data in trigger_intent["data"]
            if data.get("sentences") is sentences
        ]
    except AttributeError, KeyError, TypeError:
        return False
    if len(blocks) != 1:
        return False
    blocks[0]["lists"] = dict(lists)
    return True


def async_register_sentence_triggers(
    hass: HomeAssistant,
    groups: Sequence[SentenceGroup],
    *,
    lists: Mapping[str, Any],
    language: str,
    unparsed: TriggerCallback,
) -> Callable[[], None]:
    """
    Register groups of sentences as one trigger; each sentence answers through its group's callback.

    ``{name}`` references to ``lists`` are range or value lists; any other reference is a
    wildcard. When a sentence fits several groups equally well, the earlier group wins.
    ``unparsed`` answers a sentence Home Assistant matched but ``at`` can't parse again; it
    must answer, since None makes Home Assistant say "Done".

    Returns:
        The callback that unregisters the trigger.

    """
    wildcards = _wildcard_names(groups, lists)
    parser = Intents.from_dict(
        {
            "language": language,
            "intents": {
                f"{_GROUP_PREFIX}{index:02d}": {"data": [{"sentences": group.sentences}]}
                for index, group in enumerate(groups)
            },
            "lists": {**lists, **{name: {"wildcard": True} for name in wildcards}},
        }
    )

    async def on_trigger(user_input: ConversationInput, _result: RecognizeResult) -> str:
        given = TriggerInput(
            sentence=user_input.text,
            wildcards={},
            language=user_input.language,
            device_id=user_input.device_id,
            satellite_id=user_input.satellite_id,
            context=user_input.context,
            agent_id=user_input.agent_id,
            conversation_id=user_input.conversation_id,
        )
        match = recognize_best(user_input.text, parser)
        if match is None:
            LOGGER.debug("Sentence trigger matched but at could not parse %r", user_input.text)
            return await unparsed(given)
        given.wildcards = {name: _value_text(entity.value) for name, entity in match.entities.items()}
        given.spans = {
            name: entity.text_span for name, entity in match.entities.items() if entity.text_span is not None
        }
        return await groups[int(match.intent.name.removeprefix(_GROUP_PREFIX))].callback(given)

    manager = get_agent_manager(hass)
    sentences = [sentence for group in groups for sentence in group.sentences]
    unregister = manager.register_trigger(sentences=sentences, trigger_callback=on_trigger)
    if _inject_lists(manager, sentences, lists):
        return unregister

    unregister()
    LOGGER.warning(
        "Home Assistant's trigger storage has changed; using public-only sentence triggers, which are slower to match"
    )
    return manager.register_trigger(sentences=_spell_out_lists(sentences, lists), trigger_callback=on_trigger)
