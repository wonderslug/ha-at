"""Websocket commands the sidebar panel uses."""

from collections.abc import Callable, Coroutine
from datetime import datetime, timedelta
from functools import wraps
from typing import TYPE_CHECKING, Any

import probatio

from homeassistant.components.websocket_api import async_register_command
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.components.websocket_api.decorators import async_response, websocket_command
from homeassistant.components.websocket_api.messages import event_message
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from .const import CONF_PANEL_ADMIN_ONLY, DEFAULT_PANEL_ADMIN_ONLY, DOMAIN
from .core.actions import (
    ActionNotAllowed,
    InvalidAction,
    build_action_job,
    summarize_action,
    validate_action_config,
    validate_picked_action,
)
from .core.errors import JobNotFound, JobStateError
from .core.models import Job, JobStatus, Source, Via
from .core.timeparse import wall_time_to_utc
from .lang import get_language_pack
from .lang.en import EN
from .voice.scheduling import ScheduleRefused, async_schedule_command

if TYPE_CHECKING:
    from .core.manager import JobChange, JobManager
    from .data import AtConfigEntry

type Handler = Callable[[HomeAssistant, ActiveConnection, dict[str, Any], JobManager], Coroutine[Any, Any, None]]


def _loaded_entry(hass: HomeAssistant) -> AtConfigEntry | None:
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        return entry
    return None


def with_manager(func: Handler) -> Callable[..., Coroutine[Any, Any, None]]:
    """Look up the loaded entry's manager at call time; answer ``not_loaded`` when there is none."""

    @wraps(func)
    async def wrapper(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]) -> None:
        entry = _loaded_entry(hass)
        if entry is None:
            connection.send_error(msg["id"], "not_loaded", "at is not loaded")
            return
        await func(hass, connection, msg, entry.runtime_data.manager)

    return wrapper


def _unauthorized(connection: ActiveConnection, msg: dict[str, Any]) -> None:
    connection.send_error(msg["id"], "unauthorized", "Only an administrator can do this")


def _get_job(connection: ActiveConnection, msg: dict[str, Any], manager: JobManager, job_id: str) -> Job | None:
    """Return the job, or send ``not_found`` and return None."""
    try:
        return manager.get(job_id)
    except JobNotFound:
        connection.send_error(msg["id"], "not_found", f"No job with id {job_id}")
        return None


def _not_pending(connection: ActiveConnection, msg: dict[str, Any], job_id: str) -> None:
    connection.send_error(msg["id"], "not_pending", f"Job {job_id} is not pending")


def _parse_due(value: str) -> datetime | None:
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        return None
    return dt_util.as_utc(parsed) if parsed.tzinfo else wall_time_to_utc(parsed, dt_util.get_default_time_zone())


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    """Register every at/* command."""
    for command in (
        ws_subscribe,
        ws_parse,
        ws_schedule,
        ws_cancel,
        ws_run_now,
        ws_reschedule,
        ws_clear_history,
        ws_info,
    ):
        async_register_command(hass, command)


@websocket_command({"type": "at/subscribe"})
@async_response
@with_manager
async def ws_subscribe(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any], manager: JobManager
) -> None:
    """Send a snapshot, then every change, until the subscription ends."""
    msg_id = msg["id"]

    @callback
    def forward(change: JobChange) -> None:
        connection.send_message(event_message(msg_id, {"change": {"kind": change.kind, "job": change.job.to_dict()}}))

    @callback
    def stopped() -> None:
        connection.send_message(event_message(msg_id, {"stopped": True}))

    connection.subscriptions[msg_id] = manager.subscribe(forward, stopped)
    connection.send_result(msg_id)
    connection.send_message(
        event_message(
            msg_id,
            {
                "snapshot": {
                    "pending": [job.to_dict() for job in manager.pending()],
                    "history": [job.to_dict() for job in manager.history()],
                    "running": [job.to_dict() for job in manager.running()],
                }
            },
        )
    )


@websocket_command({"type": "at/parse", probatio.Required("text"): cv.string})
@async_response
@with_manager
async def ws_parse(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any], manager: JobManager) -> None:
    """Preview a command; never stores a job and never errors for a refusal."""
    try:
        outcome = await async_schedule_command(
            hass,
            manager,
            command_text=msg["text"],
            time_text=None,
            language=hass.config.language,
            via=Via.PANEL,
            user_id=connection.user.id,
            device_id=None,
            satellite_id=None,
            dry_run=True,
        )
    except ScheduleRefused as err:
        connection.send_result(msg["id"], {"ok": False, "message": err.speech})
        return
    connection.send_result(msg["id"], {"ok": True, "summary": outcome.job.summary, "due": outcome.job.due.isoformat()})


@websocket_command(
    {
        "type": "at/schedule",
        probatio.Optional("text"): cv.string,
        probatio.Optional("action"): [dict],
        probatio.Optional("due"): cv.string,
        probatio.Optional("delay_seconds"): probatio.All(probatio.Coerce(float), probatio.Range(min=0)),
    }
)
@async_response
@with_manager
async def ws_schedule(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any], manager: JobManager
) -> None:
    """Schedule typed text, or an action at a time."""
    msg_id = msg["id"]
    if ("text" in msg) == ("action" in msg):
        connection.send_error(msg_id, "invalid", "provide exactly one of text or action")
        return
    if "text" in msg:
        try:
            outcome = await async_schedule_command(
                hass,
                manager,
                command_text=msg["text"],
                time_text=None,
                language=hass.config.language,
                via=Via.PANEL,
                user_id=connection.user.id,
                device_id=None,
                satellite_id=None,
            )
        except ScheduleRefused as err:
            connection.send_error(msg_id, "refused", err.speech)
            return
        connection.send_result(msg_id, {"job": outcome.job.to_dict()})
        return

    if ("due" in msg) == ("delay_seconds" in msg):
        connection.send_error(msg_id, "invalid", "provide exactly one of due or delay_seconds")
        return
    if "due" in msg:
        due = _parse_due(msg["due"])
        if due is None or due < dt_util.utcnow():
            connection.send_error(msg_id, "invalid", "due must be a date and time in the future")
            return
    else:
        due = dt_util.utcnow() + timedelta(seconds=msg["delay_seconds"])

    try:
        action = validate_action_config(msg["action"])
    except probatio.Invalid as err:
        connection.send_error(msg_id, "invalid", str(err))
        return
    try:
        validate_picked_action(action, get_language_pack(hass.config.language))
        raw_action = False
    except ActionNotAllowed:
        if not connection.user.is_admin:
            _unauthorized(connection, msg)
            return
        raw_action = True
    except InvalidAction as err:
        if not connection.user.is_admin:
            connection.send_error(msg_id, "invalid", str(err))
            return
        raw_action = True
    pack = get_language_pack(hass.config.language) or EN
    job = build_action_job(
        hass,
        action,
        due=due,
        summary=summarize_action(hass, action, pack),
        raw_action=raw_action,
        via=Via.PANEL,
        user_id=connection.user.id,
    )
    job = await manager.async_add(job)
    connection.send_result(msg_id, {"job": job.to_dict()})


@websocket_command({"type": "at/cancel", probatio.Required("job_ids"): [cv.string]})
@async_response
@with_manager
async def ws_cancel(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any], manager: JobManager
) -> None:
    """Cancel pending jobs; the queue is shared, so anyone may."""
    job_ids: list[str] = msg["job_ids"]
    for job_id in job_ids:
        job = _get_job(connection, msg, manager, job_id)
        if job is None:
            return
        if job.status is not JobStatus.PENDING:
            _not_pending(connection, msg, job_id)
            return
    try:
        cancelled = await manager.async_cancel_many(job_ids, str(Via.PANEL), connection.context(msg))
    except JobStateError:
        _not_pending(connection, msg, ", ".join(job_ids))
        return
    connection.send_result(msg["id"], {"cancelled": [job.id for job in cancelled]})


@websocket_command({"type": "at/run_now", probatio.Required("job_id"): cv.string})
@async_response
@with_manager
async def ws_run_now(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any], manager: JobManager
) -> None:
    """Run a pending job now; a raw action needs an administrator."""
    job = _get_job(connection, msg, manager, msg["job_id"])
    if job is None:
        return
    if job.status is not JobStatus.PENDING:
        _not_pending(connection, msg, job.id)
        return
    if job.raw_action and not connection.user.is_admin:
        _unauthorized(connection, msg)
        return
    try:
        job = await manager.async_run_now(job.id)
    except JobStateError:
        _not_pending(connection, msg, job.id)
        return
    connection.send_result(msg["id"], {"job": job.to_dict()})


@websocket_command(
    {"type": "at/reschedule", probatio.Required("job_id"): cv.string, probatio.Required("due"): cv.string}
)
@async_response
@with_manager
async def ws_reschedule(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any], manager: JobManager
) -> None:
    """Queue a copy of a job at a new time; a raw action needs an administrator."""
    job = _get_job(connection, msg, manager, msg["job_id"])
    if job is None:
        return
    due = _parse_due(msg["due"])
    if due is None or due < dt_util.utcnow():
        connection.send_error(msg["id"], "invalid", "due must be a date and time in the future")
        return
    if job.raw_action and not connection.user.is_admin:
        _unauthorized(connection, msg)
        return
    copy = await manager.async_reschedule(job.id, due, Source(via=Via.PANEL, user_id=connection.user.id))
    connection.send_result(msg["id"], {"job": copy.to_dict()})


@websocket_command({"type": "at/clear_history"})
@async_response
@with_manager
async def ws_clear_history(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any], manager: JobManager
) -> None:
    """Delete every finished job."""
    connection.send_result(msg["id"], {"removed": await manager.async_clear_history()})


@websocket_command({"type": "at/info"})
@async_response
@with_manager
async def ws_info(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any], manager: JobManager) -> None:
    """Report what the panel needs to know about the caller and the setup."""
    entry = _loaded_entry(hass)
    panel_admin_only = (
        DEFAULT_PANEL_ADMIN_ONLY
        if entry is None
        else entry.options.get(CONF_PANEL_ADMIN_ONLY, DEFAULT_PANEL_ADMIN_ONLY)
    )
    connection.send_result(
        msg["id"],
        {
            "is_admin": connection.user.is_admin,
            "panel_admin_only": panel_admin_only,
            "language_supported": get_language_pack(hass.config.language) is not None,
        },
    )
