"""
Recognize a spoken command without running it, and check that its targets are exposed.

Uses the default agent's recognize-only path (docs/development/SPIKE-FINDINGS.md item 2):
``DefaultAgent.async_recognize_intent`` (non-strict, called once per text because of its
intent cache), then ``intent.async_match_targets(..., assistant="conversation")`` to tell an
exposed target from an unexposed or unknown one. Every private Home Assistant import the
recognizer needs lives in this module.
"""

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Any, Literal

from custom_components.at.const import INTENT_AUTOMATION_RUN, REFUSED_INTENT_PREFIX, REFUSED_INTENT_TYPES
from custom_components.at.core.models import IntentSpec, Targets
from custom_components.at.ha_internal.intent_checks import target_check
from custom_components.at.voice.automation import match_automations
from homeassistant.components import conversation
from homeassistant.exceptions import HomeAssistantError, TemplateError
from homeassistant.helpers import device_registry as dr, entity_registry as er, intent, template

# Semi-private: without it nothing can be recognized, so every command is refused with no_match.
try:
    from homeassistant.components.conversation.agent_manager import get_agent_manager
except ImportError:  # pragma: no cover - depends on the Home Assistant version
    get_agent_manager = None

# Private helpers that pick HA's own error sentence. Only the wording depends on them, so a
# Home Assistant release that renames them falls back to the language pack's wording.
try:
    from homeassistant.components.conversation.default_agent import _get_match_error_response, _get_unmatched_response
except ImportError:  # pragma: no cover - depends on the Home Assistant version
    _get_match_error_response = None
    _get_unmatched_response = None

if TYPE_CHECKING:
    from hassil.recognize import RecognizeResult

    from custom_components.at.lang import LanguagePack
    from homeassistant.components.conversation.default_agent import DefaultAgent
    from homeassistant.core import Context, HomeAssistant

ASSISTANT = conversation.DOMAIN
_NO_INTENT_KEY = "no_intent"
_MISSING_ENTITY = "<missing>"
_JSON_SCALARS = (str, int, float, bool, type(None))

type RecognizeErrorCode = Literal["no_match", "no_target", "refused"]


class RecognizeError(HomeAssistantError):
    """The command can't be scheduled: no intent, no exposed target, or a refused intent."""

    def __init__(self, code: RecognizeErrorCode, message: str) -> None:
        """Keep the reason code and the sentence to say back."""
        super().__init__(message)
        self.code: RecognizeErrorCode = code
        self.message = message


@dataclass
class RecognizedCommand:
    """An intent as Assist recognized it, what it targets, and how to describe it."""

    intent: IntentSpec
    targets: Targets
    summary: str


def is_refused_intent(intent_type: str) -> bool:
    """Return True for intents a job must not store (timers, queries, `at`'s own)."""
    return intent_type.startswith(REFUSED_INTENT_PREFIX) or intent_type in REFUSED_INTENT_TYPES


def _json_safe(value: Any) -> Any:
    if isinstance(value, _JSON_SCALARS):
        return value
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]
    return str(value)


def _slots(result: RecognizeResult) -> dict[str, Any]:
    """Build the slots the way the default agent hands them to the intent handler."""
    return {
        entity.name: {"value": _json_safe(entity.value), "text": _json_safe(entity.text or entity.value)}
        for entity in result.entities_list
    }


def _satellite_area_id(hass: HomeAssistant, device_id: str | None, satellite_id: str | None) -> str | None:
    """Return the area of the satellite or device, as the default agent finds it."""
    if satellite_id is not None and (entry := er.async_get(hass).async_get(satellite_id)) is not None:
        if entry.area_id:
            return entry.area_id
        device_id = entry.device_id
    if device_id is not None and (device := dr.async_get(hass).async_get(device_id)) is not None:
        return dr.async_get_effective_area_id(hass, device)
    return None


async def _ha_error_text(
    hass: HomeAssistant, agent: DefaultAgent, language: str, key: Any, args: dict[str, Any]
) -> str | None:
    """Render Home Assistant's own error sentence for ``key``, or None when it has none."""
    lang_intents = await agent.async_get_or_load_intents(language)
    key = getattr(key, "value", key)
    if lang_intents is None or key == _NO_INTENT_KEY or not (text := lang_intents.error_responses.get(key)):
        return None
    try:
        return str(template.Template(text, hass).async_render(args, parse_result=False))
    except TemplateError:
        return None


def _fallback_no_target(pack: LanguagePack, constraints: intent.MatchTargetsConstraints, spoken: str) -> str:
    name = constraints.name or constraints.area_name or constraints.floor_name or spoken
    domains = sorted(constraints.domains or ())
    if len(domains) == 1 and (template_text := pack.recognize_errors.get("no_target_domain")):
        return template_text.format(domain=domains[0].replace("_", " "), name=name)
    return pack.recognize_errors.get("no_target", "{name}").format(name=name)


async def _no_target_error(
    hass: HomeAssistant,
    agent: DefaultAgent,
    language: str,
    pack: LanguagePack,
    text: str,
    err: intent.MatchFailedError,
) -> RecognizeError:
    """Word a failed target match the way the default agent would."""
    message = None
    if _get_match_error_response is not None:
        key, args = _get_match_error_response(err)
        message = await _ha_error_text(hass, agent, language, key, args)
    return RecognizeError("no_target", message or _fallback_no_target(pack, err.constraints, text))


def _target_name(
    pack: LanguagePack, constraints: intent.MatchTargetsConstraints, match: intent.MatchTargetsResult
) -> str | None:
    """Name the target for the summary: the entities by name or when there is one, else the area or floor."""
    if constraints.name or constraints.single_target:
        return pack.joiner.join(state.name for state in match.states) or None
    places = [area.name for area in match.areas] or [floor.name for floor in match.floors]
    if not places:
        return None
    place = pack.joiner.join(places)
    domains = sorted(constraints.domains or ())
    things = pack.domain_words.get(domains[0]) if len(domains) == 1 else None
    return pack.place_target.format(place=place, things=things).strip() if things else place


_DETAIL_SLOTS = ("item", "search_query")


def _summary(
    pack: LanguagePack,
    intent_type: str,
    name: str | None,
    entity_ids: list[str],
    slots: dict[str, Any],
    cleaning_areas: list[str],
) -> str:
    """
    Fill the first template whose fields are all known, else the generic summary.

    Templates may use ``{name}``, the spoken ``{item}`` and ``{search_query}``, and ``{area}``,
    the areas a vacuum is asked to clean.
    """
    fields = {key: str(slots[key].get("text") or slots[key].get("value")) for key in _DETAIL_SLOTS if key in slots}
    if name:
        fields["name"] = name
    if cleaning_areas:
        fields["area"] = pack.joiner.join(cleaning_areas)
    domains = {entity_id.partition(".")[0] for entity_id in entity_ids}
    candidates = (
        pack.domain_summary_verbs.get(f"{intent_type}:{domains.pop()}") if len(domains) == 1 else None,
        pack.summary_verbs.get(intent_type),
    )
    for verb in candidates:
        if verb is None:
            continue
        try:
            return verb.format(**fields)
        except KeyError:
            continue
    return pack.generic_action_summary


def _spoken_names(slots: dict[str, Any], match: intent.MatchTargetsResult | None, by_name: bool) -> list[str]:
    names: list[str] = []
    candidates = [slots[key].get("text") for key in ("name", "area", "floor") if key in slots]
    if match is not None and by_name:
        candidates += [state.name for state in match.states]
    for candidate in candidates:
        text = str(candidate).strip() if candidate is not None else ""
        if text and text.lower() != "all" and text.lower() not in {name.lower() for name in names}:
            names.append(text)
    return names


async def _unmatched_error(
    hass: HomeAssistant, agent: DefaultAgent, result: RecognizeResult, language: str, pack: LanguagePack, text: str
) -> RecognizeError:
    """Describe a recognition whose name, area or floor matched nothing."""
    if _get_unmatched_response is None:
        unmatched = [
            spoken.strip()
            for key, entity in result.unmatched_entities.items()
            if key in {"name", "area", "floor"}
            and isinstance(spoken := getattr(entity, "text", None), str)
            and spoken.strip()
            and spoken.strip() != _MISSING_ENTITY
        ]
        name = unmatched[0] if unmatched else text
        return RecognizeError("no_target", _fallback_no_target(pack, intent.MatchTargetsConstraints(name=name), text))
    key, args = _get_unmatched_response(result)
    if getattr(key, "value", key) == _NO_INTENT_KEY:
        return RecognizeError("no_match", pack.recognize_errors.get("no_match", text))
    message = await _ha_error_text(hass, agent, language, key, args)
    unmatched_name = str(next(iter(args.values()), text))
    return RecognizeError(
        "no_target",
        message or _fallback_no_target(pack, intent.MatchTargetsConstraints(name=unmatched_name), text),
    )


def _automation_command(
    hass: HomeAssistant, pack: LanguagePack, text: str, language: str, device_id: str | None, satellite_id: str | None
) -> RecognizedCommand | None:
    """Recognize "run <automation>", which Home Assistant's own sentences don't cover."""
    if not pack.run_pattern or (found := re.fullmatch(pack.run_pattern, text.strip(), re.IGNORECASE)) is None:
        return None
    spoken = found["name"]
    match = match_automations(hass, spoken)
    if not match.is_match:
        return None
    names = pack.joiner.join(state.name for state in match.states)
    return RecognizedCommand(
        intent=IntentSpec(
            type=INTENT_AUTOMATION_RUN,
            slots={"name": {"value": spoken, "text": spoken}},
            language=language,
            device_id=device_id,
            satellite_id=satellite_id,
        ),
        targets=Targets(entity_ids=[state.entity_id for state in match.states], names=[spoken]),
        summary=pack.summary_verbs["automation.trigger"].format(name=names),
    )


async def async_recognize_command(
    hass: HomeAssistant,
    text: str,
    *,
    language: str,
    device_id: str | None,
    satellite_id: str | None,
    context: Context,
    pack: LanguagePack,
) -> RecognizedCommand:
    """
    Recognize ``text`` as Assist would, without running it.

    Returns:
        The intent to store, what it targets and a one-line summary.

    Raises:
        RecognizeError: ``no_match`` when no intent matched, ``refused`` for intents a job
            must not store, ``no_target`` when no exposed entity matches the targets.

    """
    if (command := _automation_command(hass, pack, text, language, device_id, satellite_id)) is not None:
        return command

    agent = None if get_agent_manager is None else get_agent_manager(hass).default_agent
    if agent is None:
        raise RecognizeError("no_match", pack.recognize_errors.get("no_match", text))

    # Non-strict, and only once: a strict call first poisons the agent's intent cache.
    result = await agent.async_recognize_intent(
        conversation.ConversationInput(
            text=text,
            context=context,
            conversation_id=None,
            device_id=device_id,
            satellite_id=satellite_id,
            language=language,
            agent_id=conversation.HOME_ASSISTANT_AGENT,
        )
    )
    if result is None:
        raise RecognizeError("no_match", pack.recognize_errors.get("no_match", text))

    intent_type = result.intent.name
    if is_refused_intent(intent_type):
        raise RecognizeError("refused", pack.recognize_errors.get("refused", intent_type))

    if result.unmatched_entities:
        raise await _unmatched_error(hass, agent, result, language, pack, text)

    slots = _slots(result)
    # Fix the area the default agent would prefer now, so the job prefers the same one later.
    if (area_id := _satellite_area_id(hass, device_id, satellite_id)) is not None:
        slots["preferred_area_id"] = {"value": area_id}

    try:
        check = target_check(hass, intent_type, slots)
    except intent.MatchFailedError as err:
        raise await _no_target_error(hass, agent, language, pack, text, err) from err
    constraints = check.constraints
    match: intent.MatchTargetsResult | None = None
    if constraints.has_constraints:
        match = intent.async_match_targets(hass, constraints, check.preferences)
        if not match.is_match:
            raise await _no_target_error(
                hass, agent, language, pack, text, intent.MatchFailedError(match, constraints, check.preferences)
            )

    by_name = bool(constraints.name)
    targets = Targets(
        entity_ids=[state.entity_id for state in match.states] if match else [],
        area_ids=[area.id for area in check.cleaning_areas or (match.areas if match else [])],
        floor_ids=[floor.floor_id for floor in match.floors] if match else [],
        names=_spoken_names(slots, match, by_name),
    )
    name = _target_name(pack, constraints, match) if match else None
    return RecognizedCommand(
        intent=IntentSpec(
            type=intent_type, slots=slots, language=language, device_id=device_id, satellite_id=satellite_id
        ),
        targets=targets,
        summary=_summary(
            pack, intent_type, name, targets.entity_ids, slots, [area.name for area in check.cleaning_areas]
        ),
    )


def probe() -> dict[str, bool]:
    """Report whether the private Home Assistant hooks this adapter uses resolved."""
    return {
        "get_match_error_response": _get_match_error_response is not None,
        "get_unmatched_response": _get_unmatched_response is not None,
        "get_agent_manager": callable(get_agent_manager),
    }
