"""The JSON the panel's buildPickedAction produces must pass validate_picked_action."""

import json
from pathlib import Path
from typing import Any

import pytest

from custom_components.at.core.actions import InvalidAction, validate_picked_action

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


def test_non_allowlisted_shape_still_fails() -> None:
    with pytest.raises(InvalidAction):
        validate_picked_action([{"action": "shell_command.run", "target": {"entity_id": ["light.a"]}}])
