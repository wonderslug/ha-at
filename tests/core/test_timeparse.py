"""Tests for the deterministic time phrase parser."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from custom_components.at.core.timeparse import (
    TimeParseError,
    parse_time_text,
    resolve,
    split_time_and_command,
    wall_time_to_utc,
)
from custom_components.at.lang import get_language_pack
from custom_components.at.lang.en import EN

TZ = ZoneInfo("America/Chicago")
NOW = datetime(2026, 11, 17, 22, 22, tzinfo=TZ)
FMT = "%Y-%m-%d %H:%M"


@pytest.mark.parametrize(
    ("text", "expected_local", "rolled"),
    [
        ("in 20 minutes", "2026-11-17 22:42", False),
        ("in 2 hours", "2026-11-18 00:22", False),
        ("in an hour and a half", "2026-11-17 23:52", False),
        ("in half an hour", "2026-11-17 22:52", False),
        ("in 3 days", "2026-11-20 22:22", False),
        ("at 11pm", "2026-11-17 23:00", False),
        ("at 11 pm", "2026-11-17 23:00", False),
        ("at 6am", "2026-11-18 06:00", True),
        ("at 6:30", "2026-11-18 06:30", True),
        ("at 11", "2026-11-17 23:00", False),
        ("at 7 o'clock", "2026-11-18 07:00", True),
        ("at noon", "2026-11-18 12:00", True),
        ("at midnight", "2026-11-18 00:00", False),
        ("tomorrow at 7", "2026-11-18 07:00", False),
        ("at 6:30 tonight", "2026-11-18 18:30", True),
        ("tomorrow morning at 8", "2026-11-18 08:00", False),
        ("this afternoon at 3", "2026-11-18 15:00", True),
        ("on friday at 8", "2026-11-20 08:00", False),
        ("on tuesday at 11pm", "2026-11-17 23:00", False),
        ("on tuesday at 9am", "2026-11-24 09:00", False),
    ],
)
def test_resolve_phrases(text: str, expected_local: str, rolled: bool) -> None:
    result = resolve(parse_time_text(text, EN), NOW, TZ)
    assert result.due.astimezone(TZ).strftime(FMT) == expected_local
    assert result.rolled_over == rolled
    assert result.due.tzinfo is UTC or result.due.utcoffset() == timedelta(0)


def test_relative_flag() -> None:
    assert resolve(parse_time_text("in 20 minutes", EN), NOW, TZ).relative
    assert not resolve(parse_time_text("at 11pm", EN), NOW, TZ).relative


def test_midnight_and_noon_edges() -> None:
    now = datetime(2026, 11, 17, 23, 59, tzinfo=TZ)
    for text in ("at midnight", "at 12am"):
        r = resolve(parse_time_text(text, EN), now, TZ)
        assert r.due.astimezone(TZ).strftime(FMT) == "2026-11-18 00:00"
        assert not r.rolled_over
    r = resolve(parse_time_text("at 12pm", EN), now, TZ)
    assert r.due.astimezone(TZ).strftime("%H:%M") == "12:00"


def test_dst_spring_forward_nonexistent_moves_forward() -> None:
    now = datetime(2026, 3, 7, 23, 0, tzinfo=TZ)
    r = resolve(parse_time_text("tomorrow at 2:30am", EN), now, TZ)
    assert r.due.astimezone(TZ).strftime(FMT) == "2026-03-08 03:00"


def test_dst_fall_back_ambiguous_uses_first() -> None:
    now = datetime(2026, 10, 31, 23, 0, tzinfo=TZ)
    r = resolve(parse_time_text("tomorrow at 1:30am", EN), now, TZ)
    assert r.due == datetime(2026, 11, 1, 6, 30, tzinfo=UTC)


def test_relative_is_exact_duration_across_dst() -> None:
    now = datetime(2026, 11, 1, 0, 30, tzinfo=TZ)
    r = resolve(parse_time_text("in 2 hours", EN), now, TZ)
    assert r.due - now == timedelta(hours=2)


def test_berlin_timezone() -> None:
    berlin = ZoneInfo("Europe/Berlin")
    now = datetime(2026, 11, 17, 22, 22, tzinfo=berlin)
    r = resolve(parse_time_text("tomorrow at 7", EN), now, berlin)
    assert r.due == datetime(2026, 11, 18, 6, 0, tzinfo=UTC)


def test_split_both_orders() -> None:
    cmd = "turn on the master bathroom light"
    assert split_time_and_command(f"at 11pm {cmd}", EN)[1] == cmd
    assert split_time_and_command(f"{cmd} at 11pm", EN)[1] == cmd


def test_split_keeps_command_numbers() -> None:
    _, cmd = split_time_and_command("set the living room lights to 50 percent at 6pm", EN)
    assert cmd == "set the living room lights to 50 percent"
    _, cmd = split_time_and_command("in 10 minutes turn on lamp 2", EN)
    assert cmd == "turn on lamp 2"


def test_split_day_phrases() -> None:
    spec, cmd = split_time_and_command("Turn on the porch light at 6:30 tonight", EN)
    assert cmd == "Turn on the porch light"
    assert spec.day == "today"
    assert spec.period == "night"


@pytest.mark.parametrize("text", ["at banana", "", "turn on the light", "at 25pm"])
def test_unparseable_raises(text: str) -> None:
    with pytest.raises(TimeParseError):
        parse_time_text(text, EN)
    with pytest.raises(TimeParseError):
        split_time_and_command(text, EN)


def test_get_language_pack() -> None:
    assert get_language_pack("en") is EN
    assert get_language_pack("en-GB") is EN
    assert get_language_pack("de") is None


@pytest.mark.parametrize(
    ("naive", "expected_utc"),
    [
        pytest.param("2026-03-08 02:30", "2026-03-08 08:00", id="spring-forward gap moves to 03:00 CDT"),
        pytest.param("2026-03-08 01:30", "2026-03-08 07:30", id="before the gap"),
        pytest.param("2026-03-08 03:30", "2026-03-08 08:30", id="after the gap"),
        pytest.param("2026-11-01 01:30", "2026-11-01 06:30", id="fall-back repeat takes the first"),
    ],
)
def test_wall_time_to_utc(naive: str, expected_utc: str) -> None:
    """A naive local time resolves with the parser's rule: a gap time moves to the first valid minute."""
    resolved = wall_time_to_utc(datetime.strptime(naive, FMT), TZ)
    assert resolved == datetime.strptime(expected_utc, FMT).replace(tzinfo=UTC)
