"""
Build the target check an intent's own handler will apply when the job fires.

Recognizing a sentence says which intent it is; whether the job can run depends on the targets
that intent's handler accepts. Service intents carry their required domains and features on the
handler, so those are read from it. The handlers in ``_BUILDERS`` build their constraints in code
instead, so they are mirrored here from Home Assistant's source and need re-checking when it
changes them. Required states are never checked: the state at fire time is what counts.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from custom_components.at.const import INTENT_PLACE_ANNOUNCE
from custom_components.at.voice.announce import Place, announcing_satellites, find_place, no_satellite_error
from homeassistant.components.climate.const import ClimateEntityFeature
from homeassistant.components.media_player.const import MediaPlayerEntityFeature
from homeassistant.components.vacuum.const import VacuumEntityFeature
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import area_registry as ar, floor_registry as fr, intent

ASSISTANT = "conversation"
_NO_PREFERENCES = intent.MatchTargetsPreferences()


@dataclass
class TargetCheck:
    """
    The constraints and preferences to match, and the areas or floors the command acts on, such as those to clean.

    ``states`` is set when the handler picks its targets itself rather than by matching.
    """

    constraints: intent.MatchTargetsConstraints
    preferences: intent.MatchTargetsPreferences
    areas: list[ar.AreaEntry] = field(default_factory=list)
    floors: list[fr.FloorEntry] = field(default_factory=list)
    states: list[State] | None = None


def _value(slots: dict[str, Any], key: str) -> str | None:
    value = slots.get(key, {}).get("value")
    return None if value is None else str(value)


def _values(slots: dict[str, Any], key: str) -> set[str] | None:
    if key not in slots:
        return None
    value = slots[key].get("value")
    return {str(item) for item in value} if isinstance(value, list) else {str(value)}


def _name(slots: dict[str, Any]) -> str | None:
    name = _value(slots, "name")
    return None if name == "all" else name


def _preferences(slots: dict[str, Any]) -> intent.MatchTargetsPreferences:
    return intent.MatchTargetsPreferences(
        area_id=_value(slots, "preferred_area_id"), floor_id=_value(slots, "preferred_floor_id")
    )


def _handler(hass: HomeAssistant, intent_type: str) -> intent.IntentHandler | None:
    return next((handler for handler in intent.async_get(hass) if handler.intent_type == intent_type), None)


def _service_check(hass: HomeAssistant, intent_type: str, slots: dict[str, Any]) -> TargetCheck:
    """Mirror DynamicServiceIntentHandler: a domain slot replaces the handler's required domains."""
    handler = _handler(hass, intent_type)
    service = handler if isinstance(handler, intent.DynamicServiceIntentHandler) else None
    domains = _values(slots, "domain") if "domain" in slots or service is None else service.required_domains
    return TargetCheck(
        constraints=intent.MatchTargetsConstraints(
            name=_name(slots),
            area_name=_value(slots, "area"),
            floor_name=_value(slots, "floor"),
            domains=domains,
            device_classes=_values(slots, "device_class"),
            features=None if service is None else service.required_features,
            assistant=ASSISTANT,
        ),
        preferences=_preferences(slots),
    )


def _one_entity(domain: str, features: int, *, single_target: bool) -> Callable[..., TargetCheck]:
    """Build a check for a handler that matches by name, area and floor within one domain."""

    def build(_hass: HomeAssistant, slots: dict[str, Any], _device_id: str | None) -> TargetCheck:
        return TargetCheck(
            constraints=intent.MatchTargetsConstraints(
                name=_name(slots),
                area_name=_value(slots, "area"),
                floor_name=_value(slots, "floor"),
                domains={domain},
                features=features,
                single_target=single_target,
                assistant=ASSISTANT,
            ),
            preferences=_preferences(slots),
        )

    return build


def _todo_list(_hass: HomeAssistant, slots: dict[str, Any], _device_id: str | None) -> TargetCheck:
    return TargetCheck(
        constraints=intent.MatchTargetsConstraints(name=_value(slots, "name"), domains={"todo"}, assistant=ASSISTANT),
        preferences=intent.MatchTargetsPreferences(),
    )


def _clean_area(hass: HomeAssistant, slots: dict[str, Any], _device_id: str | None) -> TargetCheck:
    """
    Mirror CleanAreaIntentHandler: the area is what to clean, the vacuum can live anywhere.

    Raises:
        intent.MatchFailedError: no area has the spoken name.

    """
    area_name = _value(slots, "area") or ""
    areas = list(intent.find_areas(area_name, ar.async_get(hass)))
    if not areas:
        raise intent.MatchFailedError(
            result=intent.MatchTargetsResult(
                is_match=False, no_match_reason=intent.MatchFailedReason.INVALID_AREA, no_match_name=area_name
            ),
            constraints=intent.MatchTargetsConstraints(area_name=area_name),
        )
    preferred = _preferences(slots)
    for attribute, value in (("id", preferred.area_id), ("floor_id", preferred.floor_id)):
        narrowed = [area for area in areas if getattr(area, attribute) == value]
        if len(areas) > 1 and value is not None and narrowed:
            areas = narrowed
    return TargetCheck(
        constraints=intent.MatchTargetsConstraints(
            name=_name(slots), domains={"vacuum"}, features=VacuumEntityFeature.CLEAN_AREA, assistant=ASSISTANT
        ),
        preferences=intent.MatchTargetsPreferences(area_id=areas[0].id, floor_id=areas[0].floor_id),
        areas=areas,
    )


def _broadcast(hass: HomeAssistant, _slots: dict[str, Any], device_id: str | None) -> TargetCheck:
    """
    Mirror BroadcastIntentHandler: every satellite that can announce, except the one spoken to.

    Raises:
        intent.MatchFailedError: no satellite would hear the broadcast.

    """
    whole_house = Place()
    if not (states := announcing_satellites(hass, skip_device_id=device_id)):
        raise no_satellite_error(whole_house)
    return TargetCheck(
        constraints=no_satellite_error(whole_house).constraints, preferences=_NO_PREFERENCES, states=states
    )


def _place_announce(hass: HomeAssistant, slots: dict[str, Any], _device_id: str | None) -> TargetCheck:
    """
    Check an announcement to one area or floor: it reaches the satellites there, the one spoken to included.

    Raises:
        intent.MatchFailedError: the place doesn't exist, or no satellite there can announce.

    """
    place = find_place(hass, slots)
    if not (states := announcing_satellites(hass, **place.satellites_filter)):
        raise no_satellite_error(place)
    return TargetCheck(
        constraints=no_satellite_error(place).constraints,
        preferences=_NO_PREFERENCES,
        areas=[place.area] if place.area else [],
        floors=[place.floor] if place.floor else [],
        states=states,
    )


_BUILDERS: dict[str, Callable[[HomeAssistant, dict[str, Any], str | None], TargetCheck]] = {
    INTENT_PLACE_ANNOUNCE: _place_announce,
    "HassBroadcast": _broadcast,
    "HassClimateSetFanMode": _one_entity("climate", ClimateEntityFeature.FAN_MODE, single_target=True),
    "HassClimateSetTemperature": _one_entity("climate", ClimateEntityFeature.TARGET_TEMPERATURE, single_target=True),
    "HassListAddItem": _todo_list,
    "HassListCompleteItem": _todo_list,
    "HassListRemoveItem": _todo_list,
    "HassMediaSearchAndPlay": _one_entity(
        "media_player",
        MediaPlayerEntityFeature.SEARCH_MEDIA | MediaPlayerEntityFeature.PLAY_MEDIA,
        single_target=True,
    ),
    "HassSetVolumeRelative": _one_entity("media_player", MediaPlayerEntityFeature.VOLUME_SET, single_target=False),
    "HassVacuumCleanArea": _clean_area,
}


def target_check(
    hass: HomeAssistant, intent_type: str, slots: dict[str, Any], device_id: str | None = None
) -> TargetCheck:
    """
    Return the check ``intent_type``'s handler will make of these slots, spoken to ``device_id``.

    Raises:
        intent.MatchFailedError: the slots name something the handler refuses before matching.

    """
    if (build := _BUILDERS.get(intent_type)) is not None:
        return build(hass, slots, device_id)
    return _service_check(hass, intent_type, slots)
