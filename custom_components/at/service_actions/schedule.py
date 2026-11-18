"""The at.schedule action."""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from custom_components.at.const import DOMAIN
from custom_components.at.core.actions import summarize_action, targets_from_action
from custom_components.at.core.models import Job, JobKind, JobStatus, Result, Source, Via, new_job_id
from custom_components.at.core.timeparse import TimeParseError, parse_time_text, resolve
from custom_components.at.lang import get_language_pack
from custom_components.at.voice.scheduling import ScheduleRefused, async_schedule_command
from homeassistant.exceptions import ServiceValidationError
from homeassistant.util import dt as dt_util

from .common import async_get_manager, async_require_admin

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse


def _invalid(key: str, **placeholders: str) -> ServiceValidationError:
    return ServiceValidationError(translation_domain=DOMAIN, translation_key=key, translation_placeholders=placeholders)


def _due_from_fields(data: dict[str, Any]) -> datetime | None:
    if (at := data.get("at")) is not None:
        return dt_util.as_utc(at)
    if (delay := data.get("delay")) is not None:
        return dt_util.utcnow() + delay
    return None


def _action_due(hass: HomeAssistant, data: dict[str, Any]) -> datetime:
    if (due := _due_from_fields(data)) is not None:
        return due
    pack = get_language_pack(hass.config.language)
    if pack is None:
        raise _invalid("unsupported_language")
    try:
        spec = parse_time_text(data["when"], pack)
        return resolve(spec, dt_util.utcnow(), ZoneInfo(hass.config.time_zone)).due
    except TimeParseError as err:
        raise _invalid("bad_time", when=data["when"]) from err


async def async_handle_schedule(hass: HomeAssistant, call: ServiceCall) -> ServiceResponse:
    """
    Schedule a command or a raw action.

    Returns:
        The new job's id, due time and summary.

    Raises:
        ServiceValidationError: the time or command was not understood.

    """
    data = call.data
    manager = async_get_manager(hass)
    user_id = call.context.user_id
    name: str | None = data.get("name")

    if "action" in data:
        await async_require_admin(hass, call)
        action: list[dict[str, Any]] = data["action"]
        pack = get_language_pack(hass.config.language)
        summary = name or (summarize_action(hass, action, pack) if pack is not None else "Run action")
        now = dt_util.utcnow()
        job = Job(
            id=new_job_id(),
            kind=JobKind.ACTION,
            status=JobStatus.PENDING,
            due=_action_due(hass, data),
            created_at=now,
            finished_at=None,
            summary=summary,
            original_text=None,
            intent=None,
            action=action,
            raw_action=True,
            targets=targets_from_action(hass, action),
            source=Source(via=Via.SERVICE, user_id=user_id),
            result=Result(),
        )
        job = await manager.async_add(job)
    else:
        try:
            outcome = await async_schedule_command(
                hass,
                manager,
                command_text=data["command"],
                time_text=data.get("when"),
                language=hass.config.language,
                via=Via.SERVICE,
                user_id=user_id,
                device_id=None,
                satellite_id=None,
                due=_due_from_fields(data),
                dry_run=True,
            )
        except ScheduleRefused as err:
            raise _invalid("schedule_refused", speech=err.speech) from err
        job = outcome.job
        if name:
            job.summary = name
        job = await manager.async_add(job)
    return {"job_id": job.id, "due": job.due.isoformat(), "summary": job.summary}
