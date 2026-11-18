"""Tests for list and cancel selection and their spoken responses."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from custom_components.at.core.models import IntentSpec, Job, JobKind, JobStatus, Result, Source, Targets, Via
from custom_components.at.core.timeparse import TimeSpec
from custom_components.at.lang import get_language_pack
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

TZ = ZoneInfo("America/Chicago")
NOW = datetime(2026, 11, 17, 20, 0, tzinfo=TZ)
PACK = get_language_pack("en")
assert PACK is not None


def _job(
    local: datetime,
    summary: str = "Turn on Porch Light",
    names: list[str] | None = None,
    via: Via = Via.VOICE,
    status: JobStatus = JobStatus.PENDING,
) -> Job:
    return Job(
        id=f"{local:%d%H%M}",
        kind=JobKind.INTENT,
        status=status,
        due=local.astimezone(UTC),
        created_at=NOW.astimezone(UTC),
        finished_at=None,
        summary=summary,
        original_text=None,
        intent=IntentSpec(type="HassTurnOn", slots={}, language="en"),
        action=None,
        raw_action=False,
        targets=Targets(names=names if names is not None else ["Porch Light"]),
        source=Source(via=via),
        result=Result(),
    )


def _at(days: int, hour: int, minute: int = 0) -> datetime:
    return (NOW + timedelta(days=days)).replace(hour=hour, minute=minute)


def test_list_scopes() -> None:
    a, b, c, d = _job(_at(0, 23)), _job(_at(1, 5)), _job(_at(1, 9)), _job(_at(7, 9))
    jobs = [d, c, b, a]
    assert select_for_list(jobs, "tonight", None, NOW, TZ) == [a, b]
    assert select_for_list(jobs, "tomorrow", None, NOW, TZ) == [b, c]
    assert select_for_list(jobs, "today", None, NOW, TZ) == [a]
    assert select_for_list(jobs, "all", None, NOW, TZ) == [a, b, c, d]
    assert select_for_list(jobs, None, None, NOW, TZ) == [a, b, c, d]
    assert select_for_list([*jobs, _job(_at(0, 22), status=JobStatus.DONE)], "all", None, NOW, TZ) == [a, b, c, d]


def test_list_by_name() -> None:
    a, b = _job(_at(0, 23)), _job(_at(0, 22), "Turn off Fan", ["Fan"])
    assert select_for_list([a, b], None, "fan", NOW, TZ) == [b]


def test_list_speech_caps_at_three() -> None:
    assert list_speech(PACK, [], NOW, TZ) == "Nothing is scheduled."
    jobs = [_job(_at(0, 21)), _job(_at(0, 22)), _job(_at(0, 23)), _job(_at(1, 6)), _job(_at(4, 8))]
    assert list_speech(PACK, jobs[:3], NOW, TZ) == (
        "3 scheduled: turn on Porch Light at 9 PM; turn on Porch Light at 10 PM; turn on Porch Light at 11 PM."
    )
    assert list_speech(PACK, jobs, NOW, TZ) == (
        "5 scheduled: turn on Porch Light at 9 PM; turn on Porch Light at 10 PM; "
        "turn on Porch Light at 11 PM, and 2 more."
    )
    assert list_speech(PACK, [jobs[3], jobs[4]], NOW, TZ) == (
        "2 scheduled: turn on Porch Light at 6 AM tomorrow; turn on Porch Light at 8 AM on Saturday."
    )


def test_cancel_by_time() -> None:
    a, b = _job(_at(0, 23)), _job(_at(1, 6))
    assert match_for_cancel([a, b], CancelQuery(time=TimeSpec(hour=6, minute=0, meridiem="am")), NOW, TZ) == [b]
    assert match_for_cancel([a, b], CancelQuery(time=TimeSpec(hour=23, minute=0, meridiem="pm")), NOW, TZ) == [a]


def test_cancel_by_name_substring() -> None:
    a, b = _job(_at(0, 23)), _job(_at(0, 22), "Turn off Fan", ["Ceiling Fan"])
    assert match_for_cancel([a, b], CancelQuery(name="porch"), NOW, TZ) == [a]
    assert match_for_cancel([a, b], CancelQuery(name="ceiling"), NOW, TZ) == [b]
    assert match_for_cancel([a, b], CancelQuery(name="turn off"), NOW, TZ) == [b]


def test_cancel_ambiguous_returns_multiple() -> None:
    names = ["Master Bathroom Light"]
    a, b = _job(_at(0, 23), names=names), _job(_at(1, 6), names=names)
    found = match_for_cancel([a, b], CancelQuery(name="master bathroom"), NOW, TZ)
    assert sorted(j.id for j in found) == sorted([a.id, b.id])
    assert ambiguous_speech(PACK, found, "master bathroom", NOW, TZ) == (
        "There are 2 jobs for Master Bathroom Light, at 11 PM today and 6 AM tomorrow. Say 'cancel the 11 PM job'."
    )
    other = _job(_at(0, 22), names=["Lamp"])
    assert ambiguous_speech(PACK, [a, other], "master bathroom", NOW, TZ) == (
        "There are 2 jobs for master bathroom, at 10 PM and 11 PM. Say 'cancel the 10 PM job'."
    )


def test_ambiguous_same_time_names_the_day_to_say() -> None:
    """Two jobs at the same time on different days: the advice says which day."""
    a, b = _job(_at(1, 6)), _job(_at(2, 6))
    assert ambiguous_speech(PACK, [b, a], None, NOW, TZ) == (
        "There are 2 jobs for Porch Light, at 6 AM tomorrow and 6 AM on Thursday. Say 'cancel the 6 AM job tomorrow'."
    )


def test_cancel_by_time_without_meridiem_matches_either_reading() -> None:
    """At 11:00, "the job at 6" is the 6 AM job tomorrow as well as one at 6 PM."""
    morning = NOW.replace(hour=11)
    six_am = _job(_at(1, 6))
    assert match_for_cancel([six_am], CancelQuery(time=TimeSpec(hour=6)), morning, TZ) == [six_am]
    six_pm = _job(_at(0, 18))
    found = match_for_cancel([six_am, six_pm], CancelQuery(time=TimeSpec(hour=6)), morning, TZ)
    assert found == [six_pm, six_am]


def test_cancel_by_time_with_day_matches_that_date() -> None:
    """A day word narrows the time to that local date."""
    tomorrow, thursday = _job(_at(1, 6)), _job(_at(2, 6))
    jobs = [tomorrow, thursday]
    assert match_for_cancel(jobs, CancelQuery(time=TimeSpec(hour=6, meridiem="am", day="tomorrow")), NOW, TZ) == [
        tomorrow
    ]
    assert match_for_cancel(jobs, CancelQuery(time=TimeSpec(hour=6, weekday=3)), NOW, TZ) == [thursday]
    assert match_for_cancel(jobs, CancelQuery(time=TimeSpec(hour=6, day="today")), NOW, TZ) == []


def test_cancel_without_criteria_matches_nothing() -> None:
    jobs = [_job(_at(0, 23)), _job(_at(1, 6))]
    assert match_for_cancel(jobs, CancelQuery(), NOW, TZ) == []
    assert match_for_cancel(jobs, CancelQuery(name=""), NOW, TZ) == []


def test_cancel_all_skips_service_jobs() -> None:
    a, b = _job(_at(0, 23)), _job(_at(0, 22), via=Via.SERVICE)
    assert match_for_cancel([a, b], CancelQuery(all=True), NOW, TZ) == [a]
    assert match_for_cancel([_job(_at(0, 23), status=JobStatus.DONE)], CancelQuery(all=True), NOW, TZ) == []


def test_cancel_speech_variants() -> None:
    job = _job(_at(0, 23))
    assert cancel_one_speech(PACK, job, NOW, TZ) == "Cancelled: turn on Porch Light at 11 PM."
    assert cancel_none_speech(PACK) == "I couldn't find a scheduled job matching that."
    assert cancel_all_speech(PACK, 3, 0) == "Cancelled 3 jobs."
    assert cancel_all_speech(PACK, 3, 2) == "Cancelled 3 jobs. 2 jobs created by automations were left alone."


def test_cancel_all_speech_singular() -> None:
    """One job is "1 job", not "1 jobs"."""
    assert cancel_all_speech(PACK, 1, 0) == "Cancelled 1 job."
    assert cancel_all_speech(PACK, 1, 1) == "Cancelled 1 job. 1 job created by automations was left alone."
    assert cancel_all_speech(PACK, 0, 2) == "Cancelled 0 jobs. 2 jobs created by automations were left alone."
