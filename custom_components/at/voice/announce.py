"""
Announcements: to every voice satellite, or only to those in one area or on one floor.

Home Assistant's broadcast intent takes nothing but a message and always reaches the whole
house, so "announce in the kitchen ..." needs an intent of its own. The language pack's
``announce_area``, ``announce_floor`` and ``announce_everyone`` sentences are parsed here with
the registries' names as real lists, which tells the place from the message that follows it.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from hassil import Intents, recognize_best
from hassil.intents import TextSlotList
import probatio

from custom_components.at.const import INTENT_PLACE_ANNOUNCE
from custom_components.at.lang import LanguagePack
from homeassistant.components.assist_satellite.const import AssistSatelliteEntityFeature
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import (
    area_registry as ar,
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
    floor_registry as fr,
    intent,
)

SATELLITE_DOMAIN = "assist_satellite"
# Mirrors EXCLUDED_DOMAINS in homeassistant/components/assist_satellite/intent.py.
_EXCLUDED_DOMAINS = frozenset({"voip"})
_PLACES = (("area", "announce_area"), ("floor", "announce_floor"))
_PLACE_SLOTS = tuple(f"{{{slot}}}" for slot, _ in _PLACES)


@dataclass(frozen=True)
class Announcement:
    """An announcement sentence as an intent and the slots to store with it."""

    intent_type: str
    slots: dict[str, Any]


def _area_of(entry: er.RegistryEntry, devices: dr.DeviceRegistry) -> str | None:
    if entry.area_id or entry.device_id is None:
        return entry.area_id
    device = devices.async_get(entry.device_id)
    return device.area_id if device is not None else None


def announcing_satellites(
    hass: HomeAssistant,
    *,
    area_id: str | None = None,
    floor_id: str | None = None,
    skip_device_id: str | None = None,
) -> list[State]:
    """
    Return the satellites an announcement reaches, as the broadcast handler picks them.

    ``area_id`` keeps those in one area, by the entity's area or else its device's, and
    ``floor_id`` those whose area is on one floor. ``skip_device_id`` leaves out the device
    the request was spoken to.
    """
    entities = er.async_get(hass)
    devices = dr.async_get(hass)
    areas = ar.async_get(hass)
    found: list[State] = []
    for entity_id in hass.states.async_entity_ids(SATELLITE_DOMAIN):
        entry = entities.async_get(entity_id)
        if entry is None or not entry.supported_features & AssistSatelliteEntityFeature.ANNOUNCE:
            continue
        if skip_device_id and entry.device_id == skip_device_id:
            continue
        config_entry = hass.config_entries.async_get_entry(entry.config_entry_id) if entry.config_entry_id else None
        if config_entry is not None and config_entry.domain in _EXCLUDED_DOMAINS:
            continue
        entity_area_id = _area_of(entry, devices)
        if area_id is not None and entity_area_id != area_id:
            continue
        if floor_id is not None:
            area = areas.async_get_area(entity_area_id) if entity_area_id else None
            if area is None or area.floor_id != floor_id:
                continue
        if (state := hass.states.get(entity_id)) is not None:
            found.append(state)
    return found


@dataclass(frozen=True)
class Place:
    """Where an announcement goes: one area or one floor, or None for the whole house."""

    area: ar.AreaEntry | None = None
    floor: fr.FloorEntry | None = None

    @property
    def satellites_filter(self) -> dict[str, str | None]:
        """The ``announcing_satellites`` arguments that keep this place's satellites."""
        return {
            "area_id": self.area.id if self.area else None,
            "floor_id": self.floor.floor_id if self.floor else None,
        }


def no_satellite_error(place: Place) -> intent.MatchFailedError:
    """Return the error for an announcement no satellite would hear."""
    return intent.MatchFailedError(
        result=intent.MatchTargetsResult(is_match=False, no_match_reason=intent.MatchFailedReason.DOMAIN),
        constraints=intent.MatchTargetsConstraints(
            area_name=place.area.name if place.area else None,
            floor_name=place.floor.name if place.floor else None,
            domains={SATELLITE_DOMAIN},
            features=AssistSatelliteEntityFeature.ANNOUNCE,
        ),
    )


def find_place(hass: HomeAssistant, slots: dict[str, Any]) -> Place:
    """
    Return the area or floor a stored id or a spoken name in ``slots`` refers to.

    Raises:
        intent.MatchFailedError: no area or floor has that id or name.

    """
    if (area_name := _slot_value(slots, "area")) is not None:
        if (area := next(iter(intent.find_areas(area_name, ar.async_get(hass))), None)) is None:
            raise intent.MatchFailedError(
                result=intent.MatchTargetsResult(
                    is_match=False, no_match_reason=intent.MatchFailedReason.INVALID_AREA, no_match_name=area_name
                ),
                constraints=intent.MatchTargetsConstraints(area_name=area_name),
            )
        return Place(area=area)
    floor_name = _slot_value(slots, "floor") or ""
    if (floor := next(iter(intent.find_floors(floor_name, fr.async_get(hass))), None)) is None:
        raise intent.MatchFailedError(
            result=intent.MatchTargetsResult(
                is_match=False, no_match_reason=intent.MatchFailedReason.INVALID_FLOOR, no_match_name=floor_name
            ),
            constraints=intent.MatchTargetsConstraints(floor_name=floor_name),
        )
    return Place(floor=floor)


def _slot_value(slots: dict[str, Any], key: str) -> str | None:
    value = slots.get(key, {}).get("value")
    return None if value is None else str(value)


_PARSERS: dict[tuple[str, str], Intents] = {}


def _parser(pack: LanguagePack, group: str) -> Intents:
    key = (pack.code, group)
    if key not in _PARSERS:
        _PARSERS[key] = Intents.from_dict(
            {
                "language": pack.code,
                "intents": {group: {"data": [{"sentences": pack.sentences.get(group, [])}]}},
                "lists": {"message": {"wildcard": True}},
            }
        )
    return _PARSERS[key]


def _place_list(hass: HomeAssistant, slot: str) -> TextSlotList:
    if slot == "area":
        names = [
            (spoken, area.id)
            for area in ar.async_get(hass).async_list_areas()
            for spoken in (area.name, *sorted(area.aliases))
        ]
    else:
        names = [
            (spoken, floor.floor_id)
            for floor in fr.async_get(hass).async_list_floors()
            for spoken in (floor.name, *sorted(floor.aliases))
        ]
    return TextSlotList.from_tuples(names, allow_template=False)


def _slot(value: str, text: str) -> dict[str, str]:
    return {"value": value, "text": text}


def _message_slot(message: str) -> dict[str, str]:
    return _slot(message.strip(), message.strip())


def parse_announcement(hass: HomeAssistant, pack: LanguagePack, text: str) -> Announcement | None:
    """
    Read ``text`` as an announcement to an area or a floor, or to everyone in words Home Assistant doesn't know.

    An area is tried before a floor, so a name both use means the area.
    """
    for slot, group in _PLACES:
        if not pack.sentences.get(group):
            continue
        found = recognize_best(text, _parser(pack, group), slot_lists={slot: _place_list(hass, slot)})
        if found is not None:
            place, message = found.entities[slot], found.entities["message"]
            return Announcement(
                INTENT_PLACE_ANNOUNCE,
                {
                    slot: _slot(str(place.value), str(place.text).strip()),
                    "message": _message_slot(str(message.value)),
                },
            )
    if pack.sentences.get("announce_everyone"):
        found = recognize_best(text, _parser(pack, "announce_everyone"))
        if found is not None:
            return Announcement(
                intent.INTENT_BROADCAST, {"message": _message_slot(str(found.entities["message"].value))}
            )
    return None


def missing_message(hass: HomeAssistant, pack: LanguagePack, text: str) -> str | None:
    """
    Read ``text`` as an announcement that names an area or a floor but says nothing to announce there.

    Home Assistant's own broadcast sentence would read the place as the message, so a cut-off
    "announce in the kitchen" must be caught before it is recognized.

    Returns:
        The pack's question asking for the message, or None when ``text`` is not such a sentence.

    """
    for slot, group in _PLACES:
        no_message = f"{group}_no_message"
        if not pack.sentences.get(no_message):
            continue
        found = recognize_best(text, _parser(pack, no_message), slot_lists={slot: _place_list(hass, slot)})
        if found is None:
            continue
        place_id = str(found.entities[slot].value)
        if slot == "area":
            area = ar.async_get(hass).async_get_area(place_id)
            name = area.name if area else str(found.entities[slot].text).strip()
        else:
            floor = fr.async_get(hass).async_get_floor(place_id)
            name = floor.name if floor else str(found.entities[slot].text).strip()
        return pack.recognize_errors[f"no_message_{slot}"].format(**{slot: name})
    return None


def _gate(sentence: str) -> str:
    ends = [sentence.index(slot) + len(slot) for slot in _PLACE_SLOTS if slot in sentence]
    return sentence[: min(ends)] if ends else sentence


def trigger_sentences(pack: LanguagePack) -> list[str]:
    """
    Return the announcement sentences for the sentence trigger.

    Home Assistant matches a trigger with every list as free text, and two free-text slots side
    by side never match, so a place sentence ends at its ``{area}`` or ``{floor}``;
    ``parse_announcement`` then reads the whole sentence again with the real names. The
    ``*_no_message`` sentences are left out: "tell {area}" alone would catch any sentence that
    starts with "tell", and the place and everyone sentences already reach each of them.
    """
    groups = [group for _, group in _PLACES] + ["announce_everyone"]
    return list(dict.fromkeys(_gate(sentence) for group in groups for sentence in pack.sentences.get(group, [])))


class PlaceAnnounceHandler(intent.IntentHandler):
    """Announce a message on the satellites in one area or on one floor, including the one spoken to."""

    intent_type = INTENT_PLACE_ANNOUNCE
    description = "Announces a message on the voice satellites in one area or on one floor"

    @property
    def slot_schema(self) -> dict:
        """The area or the floor, by id or name, and the message."""
        return {
            probatio.Exclusive("area", "place"): cv.string,
            probatio.Exclusive("floor", "place"): cv.string,
            probatio.Required("message"): cv.string,
        }

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Call assist_satellite.announce on every announcing satellite in the area or on the floor."""
        slots = self.async_validate_slots(intent_obj.slots)
        hass = intent_obj.hass
        place = find_place(hass, slots)
        if not (satellites := announcing_satellites(hass, **place.satellites_filter)):
            raise no_satellite_error(place)
        await hass.services.async_call(
            SATELLITE_DOMAIN,
            "announce",
            {"message": slots["message"]["value"]},
            blocking=True,
            context=intent_obj.context,
            target={"entity_id": [state.entity_id for state in satellites]},
        )
        if place.area is not None:
            target = intent.IntentResponseTarget(
                type=intent.IntentResponseTargetType.AREA, id=place.area.id, name=place.area.name
            )
        else:
            if TYPE_CHECKING:
                assert place.floor is not None
            target = intent.IntentResponseTarget(
                type=intent.IntentResponseTargetType.FLOOR, id=place.floor.floor_id, name=place.floor.name
            )
        response = intent_obj.create_response()
        response.async_set_results(success_results=[target])
        return response
