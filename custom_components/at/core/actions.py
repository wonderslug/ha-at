"""Picked-action rules: what a stored action may contain, and how to describe it."""

import copy
from typing import TYPE_CHECKING, Any

from custom_components.at.lang import message
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import (
    area_registry as ar,
    config_validation as cv,
    device_registry as dr,
    floor_registry as fr,
    label_registry as lr,
)
from homeassistant.util import dt as dt_util

from .models import Job, JobKind, JobStatus, Result, Source, Targets, Via, new_job_id

if TYPE_CHECKING:
    from datetime import datetime

    from custom_components.at.lang import LanguagePack
    from homeassistant.core import HomeAssistant

_TOGGLES = ("turn_on", "turn_off", "toggle")
_SCRIPT_RUN = "script.turn_on"
_AUTOMATION_TRIGGER = "automation.trigger"


class InvalidAction(HomeAssistantError):
    """The action is not one `at` allows a picked action to be; this base class means a bad shape."""


class ActionNotAllowed(InvalidAction):
    """The action is well formed but calls or targets something outside the allowlist."""


_TARGET_KEYS = frozenset({"entity_id", "area_id", "device_id", "floor_id", "label_id"})
_BROAD = frozenset({"all", "none"})


def validate_action_config(action: Any) -> list[dict[str, Any]]:
    """
    Check an action with Home Assistant's script schema without keeping the validated form.

    The schema turns templates into ``Template`` objects and delays into ``timedelta``, which cannot be
    stored; the job keeps the JSON-safe input instead and the executor validates it again when it runs.

    Returns:
        A copy of the action as given, as a list of steps.

    Raises:
        probatio.Invalid: The action is not a valid script sequence.

    """
    steps = cv.ensure_list(action)
    cv.SCRIPT_SCHEMA(copy.deepcopy(steps))
    return copy.deepcopy(steps)


def _is_template(value: Any) -> bool:
    return isinstance(value, str) and ("{{" in value or "{%" in value)


def _check_target(name: str, target: Any, pack: LanguagePack | None) -> None:
    """Allow only a dict of known keys holding explicit ids (no ``all``, no templates)."""
    if not isinstance(target, dict) or not target:
        raise InvalidAction(message(pack, "target_missing", name=name))
    if extra := set(target) - _TARGET_KEYS:
        raise InvalidAction(message(pack, "target_extra_keys", name=name, keys=", ".join(sorted(map(str, extra)))))
    for value in target.values():
        values = value if isinstance(value, list) else [value]
        if not values or not all(isinstance(item, str) and item for item in values):
            raise InvalidAction(message(pack, "target_ids_strings", name=name))
        if any(item.strip().lower() in _BROAD or _is_template(item) for item in values):
            raise ActionNotAllowed(message(pack, "target_specific", name=name))


def _check_data(data: Any, pack: LanguagePack | None) -> None:
    if not isinstance(data, dict) or set(data) - {"variables"}:
        raise ActionNotAllowed(message(pack, "data_variables_only"))
    variables = data.get("variables", {})
    if not isinstance(variables, dict):
        raise InvalidAction(message(pack, "data_variables_mapping"))
    if any(_is_template(value) for value in variables.values()):
        raise ActionNotAllowed(message(pack, "data_variables_templates"))


def validate_picked_action(action: list[dict[str, Any]], pack: LanguagePack | None = None) -> None:
    """
    Check an action against the allowlist; messages come from ``pack``, or English without one.

    Raises:
        ActionNotAllowed: The action is well formed but outside the allowlist.
        InvalidAction: The action does not have the shape a picked action needs.

    """
    if len(action) != 1:
        raise ActionNotAllowed(message(pack, "action_one_step"))
    step = action[0]
    if not isinstance(step, dict):
        raise InvalidAction(message(pack, "action_step_mapping"))
    name = step.get("action")
    if not isinstance(name, str) or "." not in name:
        raise ActionNotAllowed(message(pack, "action_step_service"))
    service = name.partition(".")[2]
    toggle = service in _TOGGLES and name != _SCRIPT_RUN
    if not (toggle or name in (_SCRIPT_RUN, _AUTOMATION_TRIGGER)):
        raise ActionNotAllowed(message(pack, "action_not_allowed", name=name))
    allowed_keys = {"action", "target"} | ({"data"} if name == _SCRIPT_RUN else set())
    if extra := set(step) - allowed_keys:
        raise ActionNotAllowed(message(pack, "action_extra_keys", name=name, keys=", ".join(sorted(extra))))
    _check_target(name, step.get("target"), pack)
    if "data" in step:
        _check_data(step["data"], pack)


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


def _area_name(hass: HomeAssistant, area_id: str) -> str:
    area = ar.async_get(hass).async_get_area(area_id)
    return area.name if area is not None else area_id


def _floor_name(hass: HomeAssistant, floor_id: str) -> str:
    floor = fr.async_get(hass).async_get_floor(floor_id)
    return floor.name if floor is not None else floor_id


def _device_name(hass: HomeAssistant, device_id: str) -> str:
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        return device_id
    return device.name_by_user or device.name or device_id


def _label_name(hass: HomeAssistant, label_id: str) -> str:
    label = lr.async_get(hass).async_get_label(label_id)
    return label.name if label is not None else label_id


def _target_names(hass: HomeAssistant, step: dict[str, Any], pack: LanguagePack) -> list[str]:
    """Name what one step targets: entities, devices, then areas and floors as one place, then labels."""
    names = [_friendly_name(hass, e) for e in _target_ids(step, "entity_id")]
    names += [_device_name(hass, d) for d in _target_ids(step, "device_id")]
    places = [_area_name(hass, a) for a in _target_ids(step, "area_id")]
    places += [_floor_name(hass, f) for f in _target_ids(step, "floor_id")]
    if places:
        place = pack.joiner.join(places)
        things = pack.domain_words.get(str(step.get("action", "")).partition(".")[0])
        names.append(pack.place_target.format(place=place, things=things).strip() if things else place)
    names += [_label_name(hass, label) for label in _target_ids(step, "label_id")]
    return names


def summarize_action(hass: HomeAssistant, action: list[dict[str, Any]], pack: LanguagePack) -> str:
    """
    Describe an action in one phrase, for example "Turn on Porch Light" or "Turn on Kitchen lights".

    Returns:
        The phrase, or the pack's generic one for anything that is not a simple targeted action.

    """
    if len(action) == 1:
        name = action[0].get("action")
        names = _target_names(hass, action[0], pack)
        if isinstance(name, str) and names:
            verb = pack.summary_verbs.get(name) or pack.summary_verbs.get(name.partition(".")[2])
            if verb:
                return verb.format(name=pack.joiner.join(names))
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


def build_action_job(
    hass: HomeAssistant,
    action: list[dict[str, Any]],
    *,
    due: datetime,
    summary: str,
    raw_action: bool,
    via: Via,
    user_id: str | None,
    origin: str | None = None,
) -> Job:
    """Build a pending ACTION job for an action list; the caller queues it."""
    now = dt_util.utcnow()
    return Job(
        id=new_job_id(),
        kind=JobKind.ACTION,
        status=JobStatus.PENDING,
        due=due,
        created_at=now,
        finished_at=None,
        summary=summary,
        original_text=None,
        intent=None,
        action=action,
        raw_action=raw_action,
        targets=targets_from_action(hass, action),
        source=Source(via=via, user_id=user_id, origin=origin),
        result=Result(),
    )
