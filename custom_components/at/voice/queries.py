"""Pure selection of jobs to read out or cancel, and the sentences that say so."""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from custom_components.at.core.models import Job, JobStatus, Via
from custom_components.at.core.timeparse import TimeSpec, resolve
from custom_components.at.lang import LanguagePack, day_qualifier

_LIST_LIMIT = 3
_TONIGHT_ENDS = time(6, 0)


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
    tz: ZoneInfo,
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
        end = datetime.combine(today + timedelta(days=1), _TONIGHT_ENDS, tzinfo=tz)
        selected = [j for j in selected if now <= j.due < end]
    if name:
        selected = [j for j in selected if _matches_name(j, name)]
    return selected


def match_for_cancel(jobs: list[Job], query: CancelQuery, now: datetime, tz: ZoneInfo) -> list[Job]:
    """Pick the pending jobs a cancel request refers to; several means it is ambiguous."""
    selected = _pending(jobs)
    if query.all:
        return [j for j in selected if j.source.via != Via.SERVICE]
    if query.time is None and not query.name:
        return []
    if query.time is not None:
        wanted = resolve(query.time, now, tz).due.astimezone(tz)
        selected = [
            j for j in selected if (local := j.due.astimezone(tz)).hour == wanted.hour and local.minute == wanted.minute
        ]
    if query.name:
        selected = [j for j in selected if _matches_name(j, query.name)]
    return selected


def _item(pack: LanguagePack, job: Job, now: datetime, tz: ZoneInfo) -> str:
    responses = pack.responses
    local_due = job.due.astimezone(tz)
    return str(responses["list_item"]).format(
        summary=job.summary[:1].lower() + job.summary[1:],
        time=responses["spoken_time"](local_due),
        day=day_qualifier(pack, local_due, now.astimezone(tz)),
    )


def list_speech(pack: LanguagePack, jobs: list[Job], now: datetime, tz: ZoneInfo) -> str:
    """Say what is scheduled: the first three, then how many more."""
    responses = pack.responses
    if not jobs:
        return str(responses["list_empty"])
    items = str(responses["list_separator"]).join(_item(pack, j, now, tz) for j in jobs[:_LIST_LIMIT])
    extra = len(jobs) - _LIST_LIMIT
    more = str(responses["list_more"]).format(more=extra) if extra > 0 else ""
    return str(responses["list"]).format(count=len(jobs), items=items, more=more)


def cancel_one_speech(pack: LanguagePack, job: Job, now: datetime, tz: ZoneInfo) -> str:
    """Say which job was cancelled."""
    return str(pack.responses["cancel_one"]).format(item=_item(pack, job, now, tz))


def cancel_none_speech(pack: LanguagePack) -> str:
    """Say that nothing matched."""
    return str(pack.responses["cancel_none"])


def ambiguous_speech(pack: LanguagePack, jobs: list[Job], query_name: str | None, tz: ZoneInfo) -> str:
    """Ask which of several matching jobs to cancel, by time."""
    responses = pack.responses
    ordered = sorted(jobs, key=lambda j: j.due.astimezone(tz).time())
    shared = set.intersection(*(set(j.targets.names) for j in ordered)) if ordered else set()
    name = next((n for n in ordered[0].targets.names if n in shared), None) if shared else None
    times = [str(responses["spoken_time"](j.due.astimezone(tz))) for j in ordered]
    return str(responses["cancel_ambiguous"]).format(
        count=len(ordered), name=name or query_name or "", times=pack.joiner.join(times), first=times[0]
    )


def cancel_all_speech(pack: LanguagePack, cancelled: int, left_alone: int) -> str:
    """Say how many were cancelled and how many automation jobs were skipped."""
    responses = pack.responses
    text = str(responses["cancel_all"]).format(count=cancelled)
    if left_alone > 0:
        text += str(responses["cancel_all_left"]).format(count=left_alone)
    return text
