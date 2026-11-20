"""The JSON the panel's buildPickedAction produces must pass validate_picked_action."""

import json
from pathlib import Path
from typing import Any

import pytest

from custom_components.at.core.actions import ActionNotAllowed, validate_picked_action

# Single source of truth, shared with frontend/test/add-job.test.ts.
CASES: list[dict[str, Any]] = json.loads(
    (Path(__file__).parent.parent / "frontend" / "test" / "picked-shapes.json").read_text()
)


def test_fixture_covers_every_shape() -> None:
    names = {step["action"] for case in CASES for step in case["expected"]}
    assert names == {
        "homeassistant.turn_on",
        "homeassistant.turn_off",
        "homeassistant.toggle",
        "script.turn_on",
        "automation.trigger",
    }


@pytest.mark.parametrize("case", CASES, ids=lambda c: json.dumps(c["expected"]))
def test_panel_shapes_validate(case: dict[str, Any]) -> None:
    validate_picked_action(case["expected"])


def test_template_in_data_still_fails() -> None:
    with pytest.raises(ActionNotAllowed):
        validate_picked_action([{"action": "light.turn_on", "data": {"brightness": "{{ 5 }}"}}])


@pytest.mark.parametrize(
    "action",
    [
        [{"action": "{{ 'light.turn_on' }}", "target": {"entity_id": "light.a"}}],
        [{"action": "notify.notify", "data": {"{{ states('sensor.x') }}": "m"}}],
    ],
)
def test_template_in_name_or_key_fails(action: list[dict[str, Any]]) -> None:
    with pytest.raises(ActionNotAllowed):
        validate_picked_action(action)
