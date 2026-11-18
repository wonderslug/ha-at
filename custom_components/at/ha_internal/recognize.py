"""
Recognize a spoken command without running it, and check that its targets are exposed.

Uses the default agent's recognize-only path (docs/development/SPIKE-FINDINGS.md item 2):
``DefaultAgent.async_recognize_intent`` (non-strict, called once per text because of its
intent cache), then ``intent.async_match_targets(..., assistant="conversation")`` to tell an
exposed target from an unexposed or unknown one. Every private Home Assistant import the
recognizer needs lives in this module.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from custom_components.at.const import REFUSED_INTENT_PREFIX, REFUSED_INTENT_TYPES
from custom_components.at.core.models import IntentSpec, Targets
from homeassistant.components import conversation
from homeassistant.components.conversation.agent_manager import get_agent_manager
from homeassistant.components.conversation.default_agent import (  # private: HA's error wording
    _get_match_error_response,
    _get_unmatched_response,
)
from homeassistant.exceptions import HomeAssistantError, TemplateError
from homeassistant.helpers import device_registry as dr, entity_registry as er, intent, template

if TYPE_CHECKING:
    from hassil.recognize import RecognizeResult

    from custom_components.at.lang import LanguagePack
    from homeassistant.components.conversation.default_agent import DefaultAgent
    from homeassistant.core import Context, HomeAssistant

ASSISTANT = conversation.DOMAIN
_NO_INTENT_KEY = "no_intent"
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


def _values(slots: dict[str, Any], key: str) -> set[str] | None:
    if key not in slots:
        return None
    value = slots[key].get("value")
    return {str(item) for item in value} if isinstance(value, list) else {str(value)}


def _constraints(slots: dict[str, Any]) -> intent.MatchTargetsConstraints:
    """Mirror the target constraints the service intent handlers build from the slots."""
    name = slots.get("name", {}).get("value")
    area = slots.get("area", {}).get("value")
    floor = slots.get("floor", {}).get("value")
    return intent.MatchTargetsConstraints(
        name=None if name in (None, "all") else str(name),
        area_name=None if area is None else str(area),
        floor_name=None if floor is None else str(floor),
        domains=_values(slots, "domain"),
        device_classes=_values(slots, "device_class"),
        assistant=ASSISTANT,
    )


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


def _target_name(
    pack: LanguagePack, constraints: intent.MatchTargetsConstraints, match: intent.MatchTargetsResult
) -> str | None:
    """Name the target for the summary: the entities by name, or the area or floor."""
    if constraints.name:
        return " and ".join(state.name for state in match.states) or None
    places = [area.name for area in match.areas] or [floor.name for floor in match.floors]
    if not places:
        return None
    place = " and ".join(places)
    domains = sorted(constraints.domains or ())
    things = pack.domain_words.get(domains[0]) if len(domains) == 1 else None
    return pack.place_target.format(place=place, things=things).strip() if things else place


def _summary(pack: LanguagePack, intent_type: str, name: str | None) -> str:
    verb = pack.summary_verbs.get(intent_type)
    return verb.format(name=name) if verb and name else pack.generic_action_summary


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
    agent = get_agent_manager(hass).default_agent
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

    slots = _slots(result)
    constraints = _constraints(slots)

    if result.unmatched_entities:
        key, args = _get_unmatched_response(result)
        if getattr(key, "value", key) == _NO_INTENT_KEY:
            raise RecognizeError("no_match", pack.recognize_errors.get("no_match", text))
        message = await _ha_error_text(hass, agent, language, key, args)
        unmatched = next(iter(args.values()), text)
        raise RecognizeError(
            "no_target",
            message or _fallback_no_target(pack, intent.MatchTargetsConstraints(name=unmatched), text),
        )

    match: intent.MatchTargetsResult | None = None
    if constraints.has_constraints:
        preferences = intent.MatchTargetsPreferences(area_id=_satellite_area_id(hass, device_id, satellite_id))
        match = intent.async_match_targets(hass, constraints, preferences)
        if not match.is_match:
            key, args = _get_match_error_response(intent.MatchFailedError(match, constraints, preferences))
            message = await _ha_error_text(hass, agent, language, key, args)
            raise RecognizeError("no_target", message or _fallback_no_target(pack, constraints, text))

    by_name = bool(constraints.name)
    targets = Targets(
        entity_ids=[state.entity_id for state in match.states] if match else [],
        area_ids=[area.id for area in match.areas] if match else [],
        floor_ids=[floor.floor_id for floor in match.floors] if match else [],
        names=_spoken_names(slots, match, by_name),
    )
    name = _target_name(pack, constraints, match) if match else None
    return RecognizedCommand(
        intent=IntentSpec(
            type=intent_type, slots=slots, language=language, device_id=device_id, satellite_id=satellite_id
        ),
        targets=targets,
        summary=_summary(pack, intent_type, name),
    )
