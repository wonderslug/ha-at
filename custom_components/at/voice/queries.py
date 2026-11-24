"""Pure selection of jobs to read out or cancel, and the sentences that say so."""

from dataclasses import dataclass
from datetime import datetime, time, timedelta, tzinfo
from typing import Literal

from custom_components.at.core.models import Job, JobStatus, Via
from custom_components.at.core.timeparse import TimeSpec, candidate_hours
from custom_components.at.lang import LanguagePack, day_qualifier, spoken_summary

_LIST_LIMIT = 3
_TONIGHT_ENDS = time(6, 0)
_RELATIVE_MIN_TOLERANCE = timedelta(minutes=1)


@dataclass
class CancelQuery:
    """What the person asked to cancel: everything, a time, a name, or a mix."""

    all: bool = False
    time: TimeSpec | None = None
    name: str | None = None


def _pending(jobs: list[Job]) -> list[Job]:
    return sorted((j for j in jobs if j.status == JobStatus.PENDING), key=lambda j: j.due)


def _matches_name(job: Job, name: str) -> bool:
    needle = name.casefold()
    return needle in job.summary.casefold() or any(needle in n.casefold() for n in job.targets.names)


def select_for_list(
    jobs: list[Job],
    scope: Literal["all", "today", "tonight", "tomorrow"] | None,
    name: str | None,
    now: datetime,
    tz: tzinfo,
) -> list[Job]:
    """Pick the pending jobs to read out, in due order."""
    local_now = now.astimezone(tz)
    today = local_now.date()
    selected = _pending(jobs)
    if scope == "today":
        selected = [j for j in selected if j.due.astimezone(tz).date() == today]
    elif scope == "tomorrow":
        selected = [j for j in selected if j.due.astimezone(tz).date() == today + timedelta(days=1)]
    elif scope == "tonight":
        end_day = today if local_now.time() < _TONIGHT_ENDS else today + timedelta(days=1)
        end = datetime.combine(end_day, _TONIGHT_ENDS, tzinfo=tz)
        selected = [j for j in selected if now <= j.due < end]
    if name:
        selected = [j for j in selected if _matches_name(j, name)]
    return selected


def _matches_time(local: datetime, spec: TimeSpec, local_now: datetime) -> bool:
    """
    Say whether a job's local due time fits a spoken clock time.

    Without a meridiem either 12-hour reading of the hour fits; a day word or weekday also
    pins the local date. A relative time ("in 20 minutes") fits a job due about that far from
    now, within a tenth of the offset and never less than a minute.
    """
    if spec.relative is not None:
        tolerance = max(_RELATIVE_MIN_TOLERANCE, spec.relative / 10)
        return abs(local - (local_now + spec.relative)) <= tolerance
    if local.minute != spec.minute or local.hour not in candidate_hours(spec):
        return False
    today = local_now.date()
    if spec.weekday is not None:
        return local.weekday() == spec.weekday
    if spec.day == "today":
        return local.date() == today
    if spec.day == "tomorrow":
        return local.date() == today + timedelta(days=1)
    return True


def match_for_cancel(jobs: list[Job], query: CancelQuery, now: datetime, tz: tzinfo) -> list[Job]:
    """Pick the pending jobs a cancel request refers to; several means it is ambiguous."""
    selected = _pending(jobs)
    if query.all:
        return [j for j in selected if j.source.via != Via.SERVICE]
    if query.time is None and not query.name:
        return []
    if query.time is not None:
        selected = [j for j in selected if _matches_time(j.due.astimezone(tz), query.time, now.astimezone(tz))]
    if query.name:
        selected = [j for j in selected if _matches_name(j, query.name)]
    return selected


def _item(pack: LanguagePack, job: Job, now: datetime, tz: tzinfo) -> str:
    responses = pack.responses
    local_due = job.due.astimezone(tz)
    return str(responses["list_item"]).format(
        summary=spoken_summary(job.summary),
        time=responses["spoken_time"](local_due),
        day=day_qualifier(pack, local_due, now.astimezone(tz)),
    )


def list_speech(pack: LanguagePack, jobs: list[Job], now: datetime, tz: tzinfo) -> str:
    """Say what is scheduled: the first three, then how many more."""
    responses = pack.responses
    if not jobs:
        return str(responses["list_empty"])
    items = str(responses["list_separator"]).join(_item(pack, j, now, tz) for j in jobs[:_LIST_LIMIT])
    extra = len(jobs) - _LIST_LIMIT
    more = str(responses["list_more"]).format(more=extra) if extra > 0 else ""
    return str(responses["list"]).format(count=len(jobs), items=items, more=more)


def cancel_one_speech(pack: LanguagePack, job: Job, now: datetime, tz: tzinfo) -> str:
    """Say which job was cancelled."""
    return str(pack.responses["cancel_one"]).format(item=_item(pack, job, now, tz))


def cancel_none_speech(pack: LanguagePack) -> str:
    """Say that nothing matched."""
    return str(pack.responses["cancel_none"])


def _spoken_day(pack: LanguagePack, local_due: datetime, local_now: datetime) -> str:
    """Say the day of a time, saying "today" too, for telling jobs on different days apart."""
    return day_qualifier(pack, local_due, local_now) or str(pack.responses["today"])


def ambiguous_speech(pack: LanguagePack, jobs: list[Job], query_name: str | None, now: datetime, tz: tzinfo) -> str:
    """Ask which of several matching jobs to cancel: by time, by day when they fall on different days, or by summary when two share a time."""
    responses = pack.responses
    local_now = now.astimezone(tz)
    ordered = sorted(jobs, key=lambda j: j.due)
    locals_ = [j.due.astimezone(tz) for j in ordered]
    shared = set.intersection(*(set(j.targets.names) for j in ordered)) if ordered else set()
    name = next((n for n in ordered[0].targets.names if n in shared), None) if shared else None
    spoken = [str(responses["spoken_time"](local)) for local in locals_]
    several_days = len({local.date() for local in locals_}) > 1
    times = [
        time + (_spoken_day(pack, local, local_now) if several_days else "")
        for time, local in zip(spoken, locals_, strict=True)
    ]
    summaries = [spoken_summary(job.summary) for job in ordered]
    if len(set(times)) < len(times) and len(set(summaries)) == len(summaries):
        items = [
            str(responses["list_item"]).format(
                summary=summary, time=time, day=_spoken_day(pack, local, local_now) if several_days else ""
            )
            for summary, time, local in zip(summaries, spoken, locals_, strict=True)
        ]
        return str(responses["cancel_ambiguous_by_summary"]).format(
            count=len(ordered), name=name or query_name or "", items=pack.joiner.join(items), first=summaries[0]
        )
    # The suggested phrase names the day only when another job shares the first job's time.
    first_day = _spoken_day(pack, locals_[0], local_now) if spoken.count(spoken[0]) > 1 else ""
    first_job = str(responses["cancel_job"]).format(time=spoken[0], day=first_day)
    return str(responses["cancel_ambiguous"]).format(
        count=len(ordered), name=name or query_name or "", times=pack.joiner.join(times), first=first_job
    )


def _plural(key: str, count: int) -> str:
    """Pick the response key for a count: ``<key>_one`` for exactly one, ``<key>`` otherwise."""
    return f"{key}_one" if count == 1 else key


def cancel_all_speech(pack: LanguagePack, cancelled: int, left_alone: int) -> str:
    """Say how many were cancelled and how many automation jobs were skipped."""
    responses = pack.responses
    text = str(responses[_plural("cancel_all", cancelled)]).format(count=cancelled)
    if left_alone > 0:
        text += str(responses[_plural("cancel_all_left", left_alone)]).format(count=left_alone)
    return text
