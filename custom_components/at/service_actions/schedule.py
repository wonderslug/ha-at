"""The at.schedule action."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from custom_components.at.const import DOMAIN
from custom_components.at.core.actions import (
    ActionNotAllowed,
    InvalidAction,
    async_summarize_action,
    build_action_job,
    classify_picked_action,
)
from custom_components.at.core.context import origin_entity_id
from custom_components.at.core.models import Via
from custom_components.at.core.timeparse import TimeParseError, parse_time_text, resolve, wall_time_to_utc
from custom_components.at.lang import get_language_pack
from custom_components.at.lang.en import EN
from custom_components.at.voice.scheduling import ScheduleRefused, async_schedule_command
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.util import dt as dt_util

from .common import async_get_manager

if TYPE_CHECKING:
    from custom_components.at.lang import LanguagePack
    from homeassistant.core import Context, HomeAssistant, ServiceCall, ServiceResponse


def _invalid(key: str, **placeholders: str) -> ServiceValidationError:
    return ServiceValidationError(translation_domain=DOMAIN, translation_key=key, translation_placeholders=placeholders)


def _due_from_fields(data: dict[str, Any]) -> datetime | None:
    if (at := data.get("at")) is not None:
        return dt_util.as_utc(at) if at.tzinfo else wall_time_to_utc(at, dt_util.get_default_time_zone())
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
        return resolve(spec, dt_util.utcnow(), dt_util.get_default_time_zone()).due
    except TimeParseError as err:
        raise _invalid("bad_time", when=data["when"]) from err


class AtActionUnauthorized(Unauthorized):
    """A non-administrator's action needs an administrator; the message says why."""

    def __init__(self, context: Context, reason: str) -> None:
        """Keep the authorization failure, and carry the reason as its translated message."""
        super().__init__(context=context)
        self.translation_domain = DOMAIN
        self.translation_key = "action_not_allowed"
        self.translation_placeholders = {"reason": reason}
        self._message = reason


async def _raw_action(
    hass: HomeAssistant, call: ServiceCall, action: list[dict[str, Any]], pack: LanguagePack | None
) -> bool:
    is_admin: bool | None = None
    if call.context.user_id is not None:
        user = await hass.auth.async_get_user(call.context.user_id)
        if user is None:
            raise Unauthorized(context=call.context)
        is_admin = user.is_admin
    try:
        return classify_picked_action(action, is_admin=is_admin, pack=pack)
    except ActionNotAllowed as err:
        raise AtActionUnauthorized(call.context, str(err)) from err
    except InvalidAction as err:
        raise _invalid("invalid_action", error=str(err)) from err


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
    origin = origin_entity_id(hass, call.context)
    name: str | None = data.get("name")

    if "action" in data:
        action: list[dict[str, Any]] = data["action"]
        pack = get_language_pack(hass.config.language)
        raw_action = await _raw_action(hass, call, action, pack)
        summary = name or await async_summarize_action(hass, action, pack or EN)
        job = build_action_job(
            hass,
            action,
            due=_action_due(hass, data),
            summary=summary,
            raw_action=raw_action,
            via=Via.SERVICE,
            user_id=user_id,
            origin=origin,
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
                origin=origin,
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
