"""Picked-action rules: what a stored action may contain, and how to describe it."""

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .models import Targets

if TYPE_CHECKING:
    from custom_components.at.lang import LanguagePack
    from homeassistant.core import HomeAssistant

_TOGGLES = ("turn_on", "turn_off", "toggle")
_SCRIPT_RUN = "script.turn_on"
_AUTOMATION_TRIGGER = "automation.trigger"


class InvalidAction(HomeAssistantError):
    """The action is not one `at` allows a picked action to be."""


def _fail(message: str) -> InvalidAction:
    return InvalidAction(message)


def validate_picked_action(action: list[dict[str, Any]]) -> None:
    """
    Check an action against the allowlist.

    Raises:
        InvalidAction: The action has the wrong shape or calls something not allowed.

    """
    if len(action) != 1:
        msg = "an action must have exactly one step"
        raise _fail(msg)
    step = action[0]
    name = step.get("action")
    if not isinstance(name, str) or "." not in name:
        msg = "the step must call a service"
        raise _fail(msg)
    service = name.partition(".")[2]
    toggle = service in _TOGGLES and name != _SCRIPT_RUN
    if not (toggle or name in (_SCRIPT_RUN, _AUTOMATION_TRIGGER)):
        msg = f"{name} is not an allowed action"
        raise _fail(msg)
    allowed_keys = {"action", "target"} | ({"data"} if name == _SCRIPT_RUN else set())
    if extra := set(step) - allowed_keys:
        msg = f"{name} does not allow {', '.join(sorted(extra))}"
        raise _fail(msg)
    if not step.get("target"):
        msg = f"{name} needs a target"
        raise _fail(msg)
    if "data" in step and (not isinstance(step["data"], dict) or set(step["data"]) - {"variables"}):
        msg = "script.turn_on only allows data.variables"
        raise _fail(msg)


def _target_ids(step: dict[str, Any], key: str) -> list[str]:
    target = step.get("target")
    if not isinstance(target, dict):
        return []
    return [value for value in cv.ensure_list(target.get(key)) if isinstance(value, str)]


def entity_ids_in(action: list[dict[str, Any]]) -> list[str]:
    """Return the entity ids that the action's steps target."""
    return [entity_id for step in action for entity_id in _target_ids(step, "entity_id")]


def _friendly_name(hass: HomeAssistant, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    return state.name if state is not None else entity_id


def summarize_action(hass: HomeAssistant, action: list[dict[str, Any]], pack: LanguagePack) -> str:
    """
    Describe an action in one phrase, for example "Turn on Porch Light".

    Returns:
        The phrase, or the pack's generic one for anything that is not a simple entity action.

    """
    if len(action) == 1:
        name = action[0].get("action")
        entity_ids = _target_ids(action[0], "entity_id")
        if isinstance(name, str) and entity_ids:
            verb = pack.summary_verbs.get(name) or pack.summary_verbs.get(name.partition(".")[2])
            if verb:
                return verb.format(name=" and ".join(_friendly_name(hass, e) for e in entity_ids))
    return pack.generic_action_summary


def targets_from_action(hass: HomeAssistant, action: list[dict[str, Any]]) -> Targets:
    """Collect what the action's steps target."""
    targets = Targets()
    for step in action:
        for entity_id in _target_ids(step, "entity_id"):
            targets.entity_ids.append(entity_id)
            targets.names.append(_friendly_name(hass, entity_id))
        targets.area_ids.extend(_target_ids(step, "area_id"))
        targets.floor_ids.extend(_target_ids(step, "floor_id"))
    return targets
