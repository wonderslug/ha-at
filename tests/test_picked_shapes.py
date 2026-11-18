"""The JSON the panel's buildPickedAction produces must pass validate_picked_action."""

import pytest

from custom_components.at.core.actions import InvalidAction, validate_picked_action

# Copied from frontend/test/add-job.test.ts (the exact objects buildPickedAction returns).
PANEL_SHAPES = [
    [{"action": "homeassistant.turn_on", "target": {"entity_id": ["light.porch"]}}],
    [{"action": "homeassistant.turn_off", "target": {"entity_id": ["light.a", "fan.b"]}}],
    [{"action": "homeassistant.toggle", "target": {"entity_id": ["light.a"]}}],
    [{"action": "script.turn_on", "target": {"entity_id": "script.movie"}}],
    [
        {
            "action": "script.turn_on",
            "target": {"entity_id": "script.movie"},
            "data": {"variables": {"level": 3}},
        }
    ],
    [{"action": "automation.trigger", "target": {"entity_id": "automation.night"}}],
]


@pytest.mark.parametrize("shape", PANEL_SHAPES)
def test_panel_shapes_validate(shape: list[dict]) -> None:
    validate_picked_action(shape)


def test_non_allowlisted_shape_still_fails() -> None:
    with pytest.raises(InvalidAction):
        validate_picked_action([{"action": "shell_command.run", "target": {"entity_id": ["light.a"]}}])
