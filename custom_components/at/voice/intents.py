"""The AtSchedule, AtList and AtCancel intents: the one code path for scheduling, listing and cancelling."""

from typing import TYPE_CHECKING, Literal, cast
from zoneinfo import ZoneInfo

import probatio

from custom_components.at.const import DOMAIN
from custom_components.at.core.models import Job, JobStatus, Via
from custom_components.at.core.timeparse import TimeParseError, parse_time_text
from custom_components.at.lang import LanguagePack, get_language_pack, message
from custom_components.at.lang.en import UNSUPPORTED_LANGUAGE
from custom_components.at.voice.queries import (
    CancelQuery,
    ambiguous_speech,
    cancel_all_speech,
    cancel_none_speech,
    cancel_one_speech,
    list_speech,
    match_for_cancel,
    select_for_list,
)
from custom_components.at.voice.scheduling import ScheduleRefused, async_schedule_command
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import intent
from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from custom_components.at.core.manager import JobManager

INTENT_SCHEDULE = "AtSchedule"
INTENT_LIST = "AtList"
INTENT_CANCEL = "AtCancel"

SCOPES = ("all", "today", "tonight", "tomorrow")

SCHEDULE_DESCRIPTION = (
    "Schedule a Home Assistant voice command to run once at a later time. Pass the user's time phrase "
    "verbatim in 'time' (e.g. 'at 6am', 'in 20 minutes', 'tomorrow at 7') and the command as a plain "
    "sentence in 'command' (e.g. 'turn on the porch light'). Never run the command yourself."
)
LIST_DESCRIPTION = (
    "List the commands scheduled to run later. Optionally narrow by 'scope' "
    "(all, today, tonight or tomorrow) or by a 'name' of what they act on."
)
CANCEL_DESCRIPTION = (
    "Cancel commands scheduled to run later. Pass 'all' true to cancel everything, or narrow by 'time' "
    "(the time phrase, e.g. 'at 6am') or by a 'name' of what the job acts on."
)


def _error(
    intent_obj: intent.Intent,
    speech: str,
    code: intent.IntentResponseErrorCode = intent.IntentResponseErrorCode.FAILED_TO_HANDLE,
) -> intent.IntentResponse:
    response = intent_obj.create_response()
    response.async_set_error(code, speech)
    return response


def _speak(intent_obj: intent.Intent, speech: str) -> intent.IntentResponse:
    response = intent_obj.create_response()
    response.async_set_speech(speech)
    return response


def _slot(intent_obj: intent.Intent, name: str) -> object:
    return intent_obj.slots.get(name, {}).get("value")


def _text_slot(intent_obj: intent.Intent, name: str) -> str | None:
    value = _slot(intent_obj, name)
    return str(value).strip() or None if value is not None else None


def _manager(hass: HomeAssistant) -> JobManager | None:
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        return cast("JobManager", entry.runtime_data.manager)
    return None


class _AtHandler(intent.IntentHandler):
    """Shared plumbing: language pack, manager lookup and the refusals."""

    def __init__(self, via: Via | None = None) -> None:
        """
        Remember how calls reach this handler.

        ``via`` of None means ask ``_via_for``; the LLM tools pass ``Via.LLM`` explicitly.
        """
        self._via = via

    def _via_for(self, _intent_obj: intent.Intent) -> Via:
        """
        Say whether the call came through the LLM API.

        Home Assistant's own IntentTool gives the handler the same Intent as a spoken call
        (platform is the conversation agent, text_input is None), so the LLM tool has to say so
        itself: it registers a handler built with ``via=Via.LLM``.
        """
        return self._via or Via.VOICE

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Resolve the language and manager, then hand over to the handler's own work."""
        try:
            self.async_validate_slots(intent_obj.slots)
        except probatio.Invalid as err:
            raise intent.InvalidSlotInfo(f"Received invalid slot info for {self.intent_type}") from err
        pack = get_language_pack(intent_obj.language)
        if pack is None:
            return _error(intent_obj, UNSUPPORTED_LANGUAGE)
        manager = _manager(intent_obj.hass)
        if manager is None:
            return _error(intent_obj, message(pack, "not_set_up"))
        try:
            return await self._async_run(intent_obj, pack, manager)
        except ScheduleRefused as err:
            # NO_INTENT_MATCH tells a sentence trigger to hand the whole sentence back to Assist.
            code = (
                intent.IntentResponseErrorCode.NO_INTENT_MATCH
                if err.unrecognized
                else intent.IntentResponseErrorCode.FAILED_TO_HANDLE
            )
            return _error(intent_obj, err.speech, code)

    async def _async_run(
        self, intent_obj: intent.Intent, pack: LanguagePack, manager: JobManager
    ) -> intent.IntentResponse:
        raise NotImplementedError


class AtScheduleHandler(_AtHandler):
    """Schedule a command for later."""

    intent_type = INTENT_SCHEDULE
    description = SCHEDULE_DESCRIPTION

    @property
    def slot_schema(self) -> dict:
        """The time phrase and the command, both required."""
        return {probatio.Required("time"): str, probatio.Required("command"): str}

    async def _async_run(
        self, intent_obj: intent.Intent, pack: LanguagePack, manager: JobManager
    ) -> intent.IntentResponse:
        outcome = await async_schedule_command(
            intent_obj.hass,
            manager,
            command_text=_text_slot(intent_obj, "command") or "",
            time_text=_text_slot(intent_obj, "time"),
            language=intent_obj.language,
            via=self._via_for(intent_obj),
            user_id=intent_obj.context.user_id,
            device_id=intent_obj.device_id,
            satellite_id=intent_obj.satellite_id,
            agent_id=intent_obj.conversation_agent_id,
        )
        return _speak(intent_obj, outcome.speech)


class AtListHandler(_AtHandler):
    """Read out what is scheduled."""

    intent_type = INTENT_LIST
    description = LIST_DESCRIPTION

    @property
    def slot_schema(self) -> dict:
        """An optional scope and an optional name."""
        return {probatio.Optional("scope"): probatio.In(SCOPES), probatio.Optional("name"): str}

    async def _async_run(
        self, intent_obj: intent.Intent, pack: LanguagePack, manager: JobManager
    ) -> intent.IntentResponse:
        tz = ZoneInfo(intent_obj.hass.config.time_zone)
        now = dt_util.utcnow()
        scope = _text_slot(intent_obj, "scope")
        jobs = select_for_list(
            manager.pending(),
            cast("Literal['all', 'today', 'tonight', 'tomorrow'] | None", scope),
            _text_slot(intent_obj, "name"),
            now,
            tz,
        )
        return _speak(intent_obj, list_speech(pack, jobs, now, tz))


class AtCancelHandler(_AtHandler):
    """Cancel scheduled jobs by time, by name, or all of them."""

    intent_type = INTENT_CANCEL
    description = CANCEL_DESCRIPTION

    @property
    def slot_schema(self) -> dict:
        """All optional: a time phrase, a name, or all."""
        return {
            probatio.Optional("time"): str,
            probatio.Optional("name"): str,
            probatio.Optional("all"): bool,
        }

    async def _async_run(
        self, intent_obj: intent.Intent, pack: LanguagePack, manager: JobManager
    ) -> intent.IntentResponse:
        tz = ZoneInfo(intent_obj.hass.config.time_zone)
        now = dt_util.utcnow()
        by = str(self._via_for(intent_obj))
        pending = manager.pending()

        if _slot(intent_obj, "all") is True:
            matches = match_for_cancel(pending, CancelQuery(all=True), now, tz)
            await manager.async_cancel_many([j.id for j in matches], by)
            left_alone = sum(1 for j in pending if j.status == JobStatus.PENDING and j.source.via == Via.SERVICE)
            return _speak(intent_obj, cancel_all_speech(pack, len(matches), left_alone))

        query = CancelQuery(name=_text_slot(intent_obj, "name"))
        if (time_text := _text_slot(intent_obj, "time")) is not None:
            try:
                query.time = parse_time_text(time_text, pack)
            except TimeParseError:
                return _error(intent_obj, str(pack.responses["bad_time"]))
        matches = match_for_cancel(pending, query, now, tz)
        if not matches:
            return _speak(intent_obj, cancel_none_speech(pack))
        if len(matches) > 1:
            return _speak(intent_obj, ambiguous_speech(pack, matches, query.name, now, tz))
        job: Job = matches[0]
        await manager.async_cancel(job.id, by)
        return _speak(intent_obj, cancel_one_speech(pack, job, now, tz))


HANDLER_TYPES = (INTENT_SCHEDULE, INTENT_LIST, INTENT_CANCEL)


@callback
def async_register_intents(hass: HomeAssistant) -> None:
    """Register the three handlers."""
    for handler in (AtScheduleHandler(), AtListHandler(), AtCancelHandler()):
        intent.async_register(hass, handler)


@callback
def async_remove_intents(hass: HomeAssistant) -> None:
    """Remove the three handlers."""
    for intent_type in HANDLER_TYPES:
        intent.async_remove(hass, intent_type)
