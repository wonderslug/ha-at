"""Recognize a command without running it, and check its targets are exposed."""

import contextlib
from dataclasses import dataclass
import json

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.at.const import REFUSED_INTENT_TYPES
from custom_components.at.ha_internal import recognize as recognize_module
from custom_components.at.ha_internal.intents import async_run_intent
from custom_components.at.ha_internal.recognize import RecognizeError, async_recognize_command
from custom_components.at.lang import get_language_pack
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.const import ATTR_FRIENDLY_NAME, EVENT_CALL_SERVICE
from homeassistant.core import Context, Event, HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
    floor_registry as fr,
)
from tests.assist import ASSISTANT, LANGUAGE, Assist  # noqa: TID251  (plain module; see tests/assist.py)

pytestmark = [
    pytest.mark.real_dependencies,
    pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning"),
]

PACK = get_language_pack(LANGUAGE)
assert PACK is not None


@dataclass
class Home:
    """The assist fixture plus a floor, a kitchen device and a master bathroom light."""

    office_device_id: str
    kitchen_device_id: str
    kitchen_area_id: str
    downstairs_floor_id: str
    service_calls: list[Event]
    initial_states: dict[str, str]


@pytest.fixture
async def home(
    hass: HomeAssistant,
    assist: Assist,
    area_registry: ar.AreaRegistry,
    floor_registry: fr.FloorRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> Home:
    """Add a Downstairs floor with the Kitchen on it, and record every service call."""
    downstairs = floor_registry.async_create("Downstairs")
    kitchen = area_registry.async_create("Kitchen", floor_id=downstairs.floor_id)
    entity_registry.async_update_entity("light.kitchen", area_id=kitchen.id)

    bathroom = entity_registry.async_get_or_create(
        "light", "test", "master_bathroom", suggested_object_id="master_bathroom", original_name="Master Bathroom Light"
    )
    hass.states.async_set(bathroom.entity_id, "off", {ATTR_FRIENDLY_NAME: "Master Bathroom Light"})
    async_expose_entity(hass, ASSISTANT, bathroom.entity_id, True)

    kitchen_entry = MockConfigEntry(domain="test")
    kitchen_entry.add_to_hass(hass)
    kitchen_device = device_registry.async_get_or_create(
        config_entry_id=kitchen_entry.entry_id, identifiers={("test", "kitchen_satellite")}
    )
    device_registry.async_update_device(kitchen_device.id, area_id=kitchen.id)

    service_calls: list[Event] = []
    hass.bus.async_listen(EVENT_CALL_SERVICE, service_calls.append)
    await hass.async_block_till_done()
    return Home(
        office_device_id=assist.device_id,
        kitchen_device_id=kitchen_device.id,
        kitchen_area_id=kitchen.id,
        downstairs_floor_id=downstairs.floor_id,
        service_calls=service_calls,
        initial_states={state.entity_id: state.state for state in hass.states.async_all("light")},
    )


async def recognize(hass: HomeAssistant, text: str, device_id: str | None):
    assert PACK is not None
    return await async_recognize_command(
        hass, text, language=LANGUAGE, device_id=device_id, satellite_id=None, context=Context(), pack=PACK
    )


def assert_nothing_ran(hass: HomeAssistant, home: Home) -> None:
    assert home.service_calls == []
    assert {state.entity_id: state.state for state in hass.states.async_all("light")} == home.initial_states


async def test_recognizes_turn_on_by_name(hass: HomeAssistant, home: Home) -> None:
    command = await recognize(hass, "turn on the master bathroom light", home.office_device_id)

    assert command.intent.type == "HassTurnOn"
    assert command.intent.language == LANGUAGE
    assert command.intent.device_id == home.office_device_id
    assert command.targets.entity_ids == ["light.master_bathroom"]
    assert "master bathroom light" in [name.lower() for name in command.targets.names]
    assert command.summary == "Turn on Master Bathroom Light"
    # The slots are stored as JSON and handed back to the intent handler as they are.
    assert json.loads(json.dumps(command.intent.slots)) == command.intent.slots
    assert command.intent.slots["name"]["value"] == "Master Bathroom Light"
    assert_nothing_ran(hass, home)


async def test_recognizes_area_and_floor(hass: HomeAssistant, home: Home) -> None:
    command = await recognize(hass, "turn off the downstairs lights", home.office_device_id)

    assert command.intent.type == "HassTurnOff"
    assert command.targets.floor_ids == [home.downstairs_floor_id]
    assert command.targets.entity_ids == ["light.kitchen"]
    assert "downstairs" in [name.lower() for name in command.targets.names]
    assert command.summary == "Turn off Downstairs lights"
    assert_nothing_ran(hass, home)


async def test_uses_satellite_area(hass: HomeAssistant, home: Home) -> None:
    command = await recognize(hass, "turn off the lights", home.kitchen_device_id)

    assert command.intent.type == "HassTurnOff"
    assert command.intent.device_id == home.kitchen_device_id
    assert command.targets.area_ids == [home.kitchen_area_id]
    assert command.targets.entity_ids == ["light.kitchen"]
    assert command.summary == "Turn off Kitchen lights"
    assert command.intent.slots["preferred_area_id"] == {"value": home.kitchen_area_id}
    assert_nothing_ran(hass, home)


async def test_satellite_area_is_kept_in_slots(
    hass: HomeAssistant, home: Home, device_registry: dr.DeviceRegistry, entity_registry: er.EntityRegistry
) -> None:
    """A satellite with its own area, on a device in no area, keeps that area for fire time."""
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(config_entry_id=entry.entry_id, identifiers={("test", "no_area")})
    satellite = entity_registry.async_get_or_create(
        "assist_satellite",
        "test",
        "kitchen_satellite",
        device_id=device.id,
        suggested_object_id="kitchen_satellite",
        original_name="Kitchen satellite",
    )
    entity_registry.async_update_entity(satellite.entity_id, area_id=home.kitchen_area_id)

    assert PACK is not None
    command = await async_recognize_command(
        hass,
        "turn off the lights",
        language=LANGUAGE,
        device_id=device.id,
        satellite_id=satellite.entity_id,
        context=Context(),
        pack=PACK,
    )

    assert command.targets.area_ids == [home.kitchen_area_id]
    assert command.intent.slots["preferred_area_id"] == {"value": home.kitchen_area_id}
    assert json.loads(json.dumps(command.intent.slots)) == command.intent.slots
    assert_nothing_ran(hass, home)


async def test_no_match(hass: HomeAssistant, home: Home) -> None:
    with pytest.raises(RecognizeError) as err:
        await recognize(hass, "make it cozy", home.office_device_id)

    assert err.value.code == "no_match"
    assert err.value.message
    assert_nothing_ran(hass, home)


async def test_unexposed_is_no_target(hass: HomeAssistant, home: Home) -> None:
    with pytest.raises(RecognizeError) as err:
        await recognize(hass, "turn on the garage light", home.office_device_id)

    assert err.value.code == "no_target"
    assert err.value.message == "Sorry, Garage light is not exposed"
    assert_nothing_ran(hass, home)


async def test_unknown_name_is_no_target(hass: HomeAssistant, home: Home) -> None:
    with pytest.raises(RecognizeError) as err:
        await recognize(hass, "turn on the zzz light", home.office_device_id)

    assert err.value.code == "no_target"
    assert err.value.message == "Sorry, I am not aware of any device called zzz"
    assert_nothing_ran(hass, home)


async def test_recognized_area_command_runs_later(hass: HomeAssistant, home: Home) -> None:
    """The stored slots, preferred area included, run through the fire-time adapter."""
    turn_off_calls = async_mock_service(hass, "light", "turn_off")
    command = await recognize(hass, "turn off the lights", home.kitchen_device_id)
    stored = json.loads(json.dumps(command.intent.slots))
    command.intent.slots = stored

    await async_run_intent(hass, command.intent, Context())

    assert [call.data["entity_id"] for call in turn_off_calls] == [["light.kitchen"]]


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("turn on the garage light", "I couldn't find anything called Garage light."),
        ("turn on the zzz light", "I couldn't find anything called zzz."),
    ],
)
async def test_no_target_without_ha_wording_helpers(
    hass: HomeAssistant, home: Home, monkeypatch: pytest.MonkeyPatch, text: str, message: str
) -> None:
    """If a Home Assistant release drops the private wording helpers, the pack's wording is used."""
    monkeypatch.setattr(recognize_module, "_get_match_error_response", None)
    monkeypatch.setattr(recognize_module, "_get_unmatched_response", None)

    with pytest.raises(RecognizeError) as err:
        await recognize(hass, text, home.office_device_id)

    assert err.value.code == "no_target"
    assert err.value.message == message
    assert_nothing_ran(hass, home)


@pytest.mark.parametrize("text", ["what's the temperature", "set a timer for 5 minutes"])
async def test_refused_intents(hass: HomeAssistant, home: Home, text: str) -> None:
    with pytest.raises(RecognizeError) as err:
        await recognize(hass, text, home.office_device_id)

    assert err.value.code == "refused"
    assert err.value.message == PACK.recognize_errors["refused"]
    assert_nothing_ran(hass, home)


def test_refused_intent_types() -> None:
    assert {
        "HassStartTimer",
        "HassCancelTimer",
        "HassCancelAllTimers",
        "HassIncreaseTimer",
        "HassDecreaseTimer",
        "HassPauseTimer",
        "HassUnpauseTimer",
        "HassTimerStatus",
        "HassGetState",
        "HassGetWeather",
        "HassGetCurrentTime",
        "HassGetCurrentDate",
        "HassNevermind",
        "HassRespond",
    } <= REFUSED_INTENT_TYPES


async def test_does_not_execute(hass: HomeAssistant, home: Home) -> None:
    for text in (
        "turn on the master bathroom light",
        "turn off the downstairs lights",
        "turn off the lights",
        "make it cozy",
        "turn on the garage light",
        "what's the temperature",
        "set a timer for 5 minutes",
    ):
        with contextlib.suppress(RecognizeError):
            await recognize(hass, text, home.kitchen_device_id)
        await hass.async_block_till_done()

    assert_nothing_ran(hass, home)
