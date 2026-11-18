"""The shared path every text entry point uses to schedule a command."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from custom_components.at.core.manager import JobManager
from custom_components.at.core.models import Job, JobKind, JobStatus, Result, Source, Via, new_job_id
from custom_components.at.core.timeparse import (
    ResolvedTime,
    TimeParseError,
    TimeSpec,
    parse_time_text,
    resolve,
    split_time_and_command,
)
from custom_components.at.ha_internal.recognize import RecognizeError, async_recognize_command
from custom_components.at.lang import LanguagePack, day_qualifier, get_language_pack

# Imported directly so the refusal is reachable when no language pack exists
from custom_components.at.lang.en import UNSUPPORTED_LANGUAGE
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util


@dataclass
class ScheduleOutcome:
    """The job that was (or, for a dry run, would be) scheduled and what to say about it."""

    job: Job
    speech: str


class ScheduleRefused(HomeAssistantError):
    """The command can't be scheduled; ``speech`` says why."""

    def __init__(self, speech: str) -> None:
        """Keep the sentence to say back."""
        super().__init__(speech)
        self.speech = speech


def _confirmation(
    pack: LanguagePack, summary: str, due: datetime, relative: timedelta | None, tz: ZoneInfo, now: datetime
) -> str:
    responses = pack.responses
    local_due = due.astimezone(tz)
    spoken = summary[:1].lower() + summary[1:]
    time = responses["spoken_time"](local_due)
    if relative is not None:
        return str(responses["relative"]).format(duration=responses["duration"](relative), time=time, summary=spoken)
    return str(responses["absolute"]).format(
        time=time, day=day_qualifier(pack, local_due, now.astimezone(tz)), summary=spoken
    )


async def async_schedule_command(
    hass: HomeAssistant,
    manager: JobManager,
    *,
    command_text: str,
    time_text: str | None,
    language: str,
    via: Via,
    user_id: str | None,
    device_id: str | None,
    satellite_id: str | None,
    agent_id: str | None = None,
    due: datetime | None = None,
    dry_run: bool = False,
) -> ScheduleOutcome:
    """
    Schedule a spoken or typed command for later.

    Returns:
        The job and the sentence confirming it. With ``dry_run`` the job is not saved.

    Raises:
        ScheduleRefused: the language is unsupported, the time or command was not understood,
            or the command can't be checked right now.

    """
    pack = get_language_pack(language)
    if pack is None:
        raise ScheduleRefused(UNSUPPORTED_LANGUAGE)

    tz = ZoneInfo(hass.config.time_zone)
    now = dt_util.utcnow()
    spec: TimeSpec | None = None
    resolved: ResolvedTime | None = None
    recognize_text = command_text
    if due is None:
        try:
            if time_text is None:
                spec, recognize_text = split_time_and_command(command_text, pack)
            else:
                spec = parse_time_text(time_text, pack)
            resolved = resolve(spec, now, tz)
        except TimeParseError as err:
            raise ScheduleRefused(str(pack.responses["bad_time"])) from err
        due = resolved.due

    try:
        command = await async_recognize_command(
            hass,
            recognize_text,
            language=language,
            device_id=device_id,
            satellite_id=satellite_id,
            context=Context(user_id=user_id),
            pack=pack,
        )
    except RecognizeError as err:
        raise ScheduleRefused(err.message) from err

    job = Job(
        id=new_job_id(),
        kind=JobKind.INTENT,
        status=JobStatus.PENDING,
        due=due,
        created_at=now,
        finished_at=None,
        summary=command.summary,
        original_text=command_text,
        intent=command.intent,
        action=None,
        raw_action=False,
        targets=command.targets,
        source=Source(via=via, user_id=user_id, device_id=device_id, agent_id=agent_id),
        result=Result(),
    )
    relative = spec.relative if resolved is not None and resolved.relative and spec is not None else None
    speech = _confirmation(pack, command.summary, due, relative, tz, now)
    if not dry_run:
        job = await manager.async_add(job)
    return ScheduleOutcome(job=job, speech=speech)
