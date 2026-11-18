"""Tests for the picked-action allowlist and its summaries."""

import dataclasses
from typing import Any

import pytest

from custom_components.at.core.actions import (
    InvalidAction,
    summarize_action,
    targets_from_action,
    validate_picked_action,
)
from custom_components.at.core.models import Targets
from custom_components.at.lang import get_language_pack
from custom_components.at.lang.en import EN
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant

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
    ],
)
def test_validate_picked_action_allows_shapes(action: list[dict[str, Any]]) -> None:
    """Every allowed shape passes."""
    validate_picked_action(action)


@pytest.mark.parametrize(
    "action",
    [
        step("light.turn_on", target={"entity_id": "light.porch"}, data={"brightness": 10}),
        step("light.turn_on", target={"entity_id": "light.porch"}, data={}),
        step("shell_command.x", target={"entity_id": "light.porch"}),
        step("light.turn_on"),
        step("light.turn_on", target={}),
        step("light.turn_on", target={"entity_id": "light.porch"}, enabled=False),
        step("script.turn_on", target={"entity_id": "script.a"}, data={"variables": {}, "other": 1}),
        step("script.turn_on", target={"entity_id": "script.a"}, data={"other": 1}),
        step("automation.trigger", target={"entity_id": "automation.a"}, data={"variables": {}}),
        step("light.set_color", target={"entity_id": "light.porch"}),
        step("light.turn_on", target="all"),
        step("light.turn_on", target={"entity_id": "all"}),
        step("light.turn_on", target={"entity_id": ["light.a", "NONE"]}),
        step("light.turn_on", target="light.porch"),
        step("light.turn_on", target={"entity_id": "{{ states.light | map(attribute='entity_id') | list }}"}),
        step("light.turn_on", target={"area_id": "{% if true %}office{% endif %}"}),
        step("light.turn_on", target={"entity_id": 5}),
        step("light.turn_on", target={"entity_id": []}),
        step("light.turn_on", target={"entity_id": "light.a", "bogus": "x"}),
        step("script.turn_on", target={"entity_id": "script.a"}, data={"variables": "x"}),
        step("script.turn_on", target={"entity_id": "script.a"}, data={"variables": {"m": "{{ 1 }}"}}),
        step("script.turn_on", target={"entity_id": "script.a"}, data="x"),
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
