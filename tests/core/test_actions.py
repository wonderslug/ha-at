"""Tests for the picked-action allowlist and its summaries."""

import dataclasses
from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.at.core.actions import (
    ActionNotAllowed,
    InvalidAction,
    async_service_name,
    async_summarize_action,
    classify_picked_action,
    summarize_action,
    targets_from_action,
    validate_picked_action,
)
from custom_components.at.core.models import Targets
from custom_components.at.lang import get_language_pack
from custom_components.at.lang.en import EN
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, device_registry as dr, floor_registry as fr, label_registry as lr
from homeassistant.setup import async_setup_component

PACK = get_language_pack("en")
assert PACK is not None


def step(action: str, **rest: Any) -> list[dict[str, Any]]:
    """Build a one-step action list."""
    return [{"action": action, **rest}]


@pytest.mark.parametrize(
    "action",
    [
        step("homeassistant.turn_on", target={"entity_id": "light.porch"}),
        step("homeassistant.turn_off", target={"entity_id": ["light.a", "light.b"]}),
        step("homeassistant.toggle", target={"area_id": "office"}),
        step("light.turn_on", target={"entity_id": "light.porch"}),
        step("switch.toggle", target={"entity_id": "switch.fan"}),
        step("script.turn_on", target={"entity_id": "script.bedtime"}),
        step("script.turn_on", target={"entity_id": "script.bedtime"}, data={"variables": {"msg": "hi"}}),
        step("automation.trigger", target={"entity_id": "automation.morning"}),
        step("climate.set_temperature", target={"area_id": "living_room"}, data={"temperature": 21}),
        step("persistent_notification.create", data={"message": "Hi", "title": "At"}),
        step("light.turn_on", target={"entity_id": ["light.a"]}, data={"rgb_color": [255, 0, 0]}),
        step("notify.notify", data={"message": "x", "data": {"tag": "a"}}),
        step("light.turn_on", target={"entity_id": "light.porch"}, data={"brightness": 10}),
        step("light.turn_on", target={"entity_id": "light.porch"}, data={}),
        step("shell_command.x", target={"entity_id": "light.porch"}),
        step("light.turn_on"),
    ],
)
def test_validate_picked_action_allows_shapes(action: list[dict[str, Any]]) -> None:
    """Every allowed shape passes."""
    validate_picked_action(action)


@pytest.mark.parametrize(
    "action",
    [
        step("light.turn_on", target={}),
        step("light.turn_on", target={"entity_id": "light.porch"}, enabled=False),
        step("light.turn_on", target="all"),
        step("light.turn_on", target={"entity_id": "all"}),
        step("light.turn_on", target={"entity_id": ["light.a", "NONE"]}),
        step("light.turn_on", target="light.porch"),
        step("light.turn_on", target={"entity_id": "{{ states.light | map(attribute='entity_id') | list }}"}),
        step("light.turn_on", target={"area_id": "{% if true %}office{% endif %}"}),
        step("light.turn_on", target={"entity_id": 5}),
        step("light.turn_on", target={"entity_id": []}),
        step("light.turn_on", target={"entity_id": "light.a", "bogus": "x"}),
        step("light.turn_on", data=["not", "a", "mapping"]),
        ["light.turn_on"],
        [{"delay": 5}],
        [],
        [
            {"action": "light.turn_on", "target": {"entity_id": "light.a"}},
            {"action": "light.turn_off", "target": {"entity_id": "light.a"}},
        ],
    ],
)
def test_validate_picked_action_rejects(action: list[dict[str, Any]]) -> None:
    """Anything off the allowlist is rejected."""
    with pytest.raises(InvalidAction):
        validate_picked_action(action)


@pytest.mark.parametrize(
    "action",
    [
        step("light.turn_on", target={"entity_id": "light.a"}, data={"rgb_color": ["{{ 1 }}", 0, 0]}),
        step("notify.notify", data={"message": {"title": "{% if x %}y{% endif %}"}}),
        step("light.turn_off", data={"entity_id": "all"}),
        step("light.turn_off", target={"entity_id": "all"}),
        step("light.turn_on", target={"entity_id": "light.a"}, continue_on_error=True),
        step("{{ 'light.turn_on' }}", target={"entity_id": "light.a"}),
        step("notify.notify", data={"{{ states('sensor.x') }}": "m"}),
        step("notify.notify", data={"data": {"{% if x %}k{% endif %}": "v"}}),
        [
            {"action": "light.turn_on", "target": {"entity_id": "light.a"}},
            {"delay": 5},
        ],
        [{"delay": 5}],
    ],
)
def test_validate_picked_action_admin_only(action: list[dict[str, Any]]) -> None:
    """Well-formed content that only an administrator may schedule."""
    with pytest.raises(ActionNotAllowed):
        validate_picked_action(action)


def test_validate_picked_action_templated_name_says_why() -> None:
    """A templated action name is refused with the templates message, not as a bad service."""
    with pytest.raises(ActionNotAllowed, match="Templates are only available to administrators"):
        validate_picked_action(step("{{ 'light.turn_on' }}", target={"entity_id": "light.a"}))


def test_validate_picked_action_malformed_data_target_is_invalid() -> None:
    """An empty id list in data is a bad shape, not something an administrator may do."""
    with pytest.raises(InvalidAction) as err:
        validate_picked_action(step("light.turn_on", data={"entity_id": []}))
    assert not isinstance(err.value, ActionNotAllowed)


PLAIN = step("light.turn_on", target={"entity_id": "light.a"})
TEMPLATED = step("light.turn_on", target={"entity_id": "light.a"}, data={"brightness": "{{ 5 }}"})
MISSHAPEN = step("light.turn_on", target={})


@pytest.mark.parametrize(
    ("action", "is_admin", "raw_action"),
    [
        (PLAIN, None, True),
        (TEMPLATED, None, True),
        (MISSHAPEN, None, True),
        (PLAIN, True, True),
        (TEMPLATED, True, True),
        (MISSHAPEN, True, True),
        (PLAIN, False, False),
    ],
)
def test_classify_picked_action(action: list[dict[str, Any]], is_admin: bool | None, raw_action: bool) -> None:
    """No user or an administrator makes the job admin-only; a non-admin's plain step does not."""
    assert classify_picked_action(action, is_admin=is_admin, pack=PACK) is raw_action


def test_classify_picked_action_non_admin_refusals() -> None:
    """A non-admin gets ActionNotAllowed for admin-only content and InvalidAction for a bad shape."""
    with pytest.raises(ActionNotAllowed, match="Templates are only available to administrators"):
        classify_picked_action(TEMPLATED, is_admin=False, pack=PACK)
    with pytest.raises(InvalidAction) as err:
        classify_picked_action(MISSHAPEN, is_admin=False, pack=PACK)
    assert not isinstance(err.value, ActionNotAllowed)


async def test_summarize_action(hass: HomeAssistant) -> None:
    """Summaries use friendly names and fall back to the entity id."""
    hass.states.async_set("light.porch", "off", {ATTR_FRIENDLY_NAME: "Porch Light"})
    hass.states.async_set("script.bedtime", "off", {ATTR_FRIENDLY_NAME: "Bedtime"})
    hass.states.async_set("automation.morning", "on", {ATTR_FRIENDLY_NAME: "Morning Routine"})
    porch = {"entity_id": "light.porch"}
    expected = {
        "Turn on Porch Light": step("light.turn_on", target=porch),
        "Turn off Porch Light": step("homeassistant.turn_off", target=porch),
        "Toggle Porch Light": step("light.toggle", target=porch),
        "Run Bedtime": step("script.turn_on", target={"entity_id": "script.bedtime"}),
        "Trigger Morning Routine": step("automation.trigger", target={"entity_id": "automation.morning"}),
        "Turn on switch.unknown": step("switch.turn_on", target={"entity_id": "switch.unknown"}),
        "Turn on Porch Light and switch.unknown": step(
            "homeassistant.turn_on", target={"entity_id": ["light.porch", "switch.unknown"]}
        ),
        "Run action": [{"delay": 5}],
    }
    for summary, action in expected.items():
        assert summarize_action(hass, action, PACK) == summary


async def test_summarize_action_names_places_devices_and_labels(hass: HomeAssistant) -> None:
    """Areas and floors read like a voice summary; devices and labels use their names; unknown ids stay ids."""
    kitchen = ar.async_get(hass).async_create("Kitchen")
    upstairs = fr.async_get(hass).async_create("Upstairs")
    holiday = lr.async_get(hass).async_create("Holiday")
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)
    lamp = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("test", "lamp")}, name="Desk Lamp"
    )
    expected = {
        "Turn on Kitchen lights": step("light.turn_on", target={"area_id": kitchen.id}),
        "Turn off Kitchen and Upstairs lights": step(
            "light.turn_off", target={"area_id": kitchen.id, "floor_id": upstairs.floor_id}
        ),
        "Turn on Kitchen": step("homeassistant.turn_on", target={"area_id": kitchen.id}),
        "Toggle Desk Lamp": step("switch.toggle", target={"device_id": lamp.id}),
        "Turn on Holiday": step("homeassistant.turn_on", target={"label_id": holiday.label_id}),
        "Turn on gone_area lights": step("light.turn_on", target={"area_id": "gone_area"}),
    }
    for summary, action in expected.items():
        assert summarize_action(hass, action, PACK) == summary


async def test_targets_from_action(hass: HomeAssistant) -> None:
    """Targets carry entity ids, areas, floors and friendly names."""
    hass.states.async_set("light.porch", "off", {ATTR_FRIENDLY_NAME: "Porch Light"})
    action = step(
        "homeassistant.turn_off",
        target={"entity_id": ["light.porch", "switch.x"], "area_id": "office", "floor_id": ["up"]},
    )
    assert targets_from_action(hass, action) == Targets(
        entity_ids=["light.porch", "switch.x"],
        area_ids=["office"],
        floor_ids=["up"],
        names=["Porch Light", "switch.x"],
    )
    assert targets_from_action(hass, [{"delay": 5}]) == Targets()


def test_messages_come_from_the_pack_with_english_fallback() -> None:
    """A pack's own wording is used; a key it lacks falls back to English."""
    pack = dataclasses.replace(EN, messages={"action_one_step": "une seule étape"})
    with pytest.raises(InvalidAction, match="une seule étape"):
        validate_picked_action([], pack)
    with pytest.raises(InvalidAction, match="the step must call a service"):
        validate_picked_action([{"delay": 1}], pack)


async def test_summarize_action_with_service_name(hass: HomeAssistant) -> None:
    """A translated service name backs up actions without a known verb; a known verb still wins."""
    hass.states.async_set("climate.living_room", "off", {ATTR_FRIENDLY_NAME: "Living Room"})
    hass.states.async_set("light.porch", "off", {ATTR_FRIENDLY_NAME: "Porch Light"})
    climate = step("climate.set_temperature", target={"entity_id": "climate.living_room"})
    notify = step("persistent_notification.create", data={"message": "hi"})
    light = step("light.turn_on", target={"entity_id": "light.porch"})
    assert summarize_action(hass, climate, PACK, service_name="Set temperature") == "Set temperature: Living Room"
    assert summarize_action(hass, notify, PACK, service_name="Create") == "Create"
    assert summarize_action(hass, light, PACK, service_name="Turn on") == "Turn on Porch Light"
    assert summarize_action(hass, climate + notify, PACK, service_name="Create") == EN.generic_action_summary


async def test_async_service_name(hass: HomeAssistant) -> None:
    """The service name comes from the translations of the integration that owns it."""
    assert await async_setup_component(hass, "light", {})
    name = await async_service_name(hass, "light.turn_on")
    assert name
    assert await async_service_name(hass, "nope.nothing") is None
    assert await async_service_name(hass, "malformed") is None


async def test_async_summarize_action(hass: HomeAssistant) -> None:
    """The async summary looks up the name of a single step's service."""
    assert await async_setup_component(hass, "light", {})
    hass.states.async_set("light.porch", "off", {ATTR_FRIENDLY_NAME: "Porch Light"})
    assert await async_summarize_action(hass, step("light.toggle", target={"entity_id": "light.porch"}), PACK) == (
        "Toggle Porch Light"
    )
    assert await async_summarize_action(hass, [{"delay": 5}], PACK) == EN.generic_action_summary
    assert await async_summarize_action(hass, step("nope.nothing"), PACK) == EN.generic_action_summary
