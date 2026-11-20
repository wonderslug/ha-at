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
    ("text", "expected_local"),
    [
        ("in 20 minutes", "2026-11-17 22:42"),
        ("in 2 hours", "2026-11-18 00:22"),
        ("in an hour and a half", "2026-11-17 23:52"),
        ("in half an hour", "2026-11-17 22:52"),
        ("in 3 days", "2026-11-20 22:22"),
        ("at 11pm", "2026-11-17 23:00"),
        ("at 11 pm", "2026-11-17 23:00"),
        ("at 6am", "2026-11-18 06:00"),
        ("at 6:30", "2026-11-18 06:30"),
        ("at 11", "2026-11-17 23:00"),
        ("at 7 o'clock", "2026-11-18 07:00"),
        ("at noon", "2026-11-18 12:00"),
        ("at midnight", "2026-11-18 00:00"),
        ("tomorrow at 7", "2026-11-18 07:00"),
        ("at 6:30 tonight", "2026-11-18 18:30"),
        ("tomorrow morning at 8", "2026-11-18 08:00"),
        ("this afternoon at 3", "2026-11-18 15:00"),
        ("on friday at 8", "2026-11-20 08:00"),
        ("on tuesday at 11pm", "2026-11-17 23:00"),
        ("on tuesday at 9am", "2026-11-24 09:00"),
    ],
)
def test_resolve_phrases(text: str, expected_local: str) -> None:
    result = resolve(parse_time_text(text, EN), NOW, TZ)
    assert result.due.astimezone(TZ).strftime(FMT) == expected_local
    assert result.due.tzinfo is UTC or result.due.utcoffset() == timedelta(0)


def test_relative_flag() -> None:
    assert resolve(parse_time_text("in 20 minutes", EN), NOW, TZ).relative
    assert not resolve(parse_time_text("at 11pm", EN), NOW, TZ).relative


def test_midnight_and_noon_edges() -> None:
    now = datetime(2026, 11, 17, 23, 59, tzinfo=TZ)
    for text in ("at midnight", "at 12am"):
        r = resolve(parse_time_text(text, EN), now, TZ)
        assert r.due.astimezone(TZ).strftime(FMT) == "2026-11-18 00:00"
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


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        ("in twenty minutes", 20),
        ("in seventeen minutes", 17),
        ("in forty five minutes", 45),
        ("in forty-five minutes", 45),
        ("in Twenty Five minutes", 25),
        ("in ninety minutes", 90),
        ("in a hundred minutes", 100),
        ("in one hundred twenty minutes", 120),
        ("in one hundred and twenty minutes", 120),
        ("in two hundred and five minutes", 205),
        ("in twenty one and a half minutes", 21.5),
        ("in one hundred and fifty five hours", 155 * 60),
    ],
)
def test_compound_number_words(text: str, minutes: float) -> None:
    assert parse_time_text(text, EN).relative == timedelta(minutes=minutes)


@pytest.mark.parametrize(
    ("text", "expected_local"),
    [
        ("at seven", "2026-11-18 07:00"),
        ("at seven thirty", "2026-11-18 07:30"),
        ("at six forty five pm", "2026-11-18 18:45"),
        ("at six forty-five pm", "2026-11-18 18:45"),
        ("at seven oh five", "2026-11-18 07:05"),
        ("at seven o five am", "2026-11-18 07:05"),
        ("at nine o'clock", "2026-11-18 09:00"),
        ("at eleven fifteen", "2026-11-17 23:15"),
        ("at twenty two thirty", "2026-11-17 22:30"),
        ("at one twenty", "2026-11-18 01:20"),
        ("tomorrow at seven fifteen", "2026-11-18 07:15"),
        ("at eight thirty tonight", "2026-11-18 20:30"),
        ("on friday at ten", "2026-11-20 10:00"),
    ],
)
def test_clock_time_in_words(text: str, expected_local: str) -> None:
    result = resolve(parse_time_text(text, EN), NOW, TZ)
    assert result.due.astimezone(TZ).strftime(FMT) == expected_local


def test_split_clock_time_in_words() -> None:
    cmd = "turn on the master bathroom light"
    spec, rest = split_time_and_command(f"{cmd} at seven thirty", EN)
    assert (rest, spec.hour, spec.minute) == (cmd, 7, 30)
    spec, rest = split_time_and_command(f"at six forty five pm {cmd}", EN)
    assert (rest, spec.hour, spec.minute) == (cmd, 18, 45)
    spec, rest = split_time_and_command("set the volume to forty in forty five minutes", EN)
    assert (rest, spec.relative) == ("set the volume to forty", timedelta(minutes=45))


def test_sentence_list_words_parse_to_their_value() -> None:
    """Whatever the voice sentence lists offer, the parser reads as the same number."""
    lists = EN.sentence_lists
    for value in lists["number_word"]["values"]:
        assert parse_time_text(f"in {value['in']} minutes", EN).relative == timedelta(minutes=value["out"])
    for value in lists["hour_word"]["values"]:
        assert parse_time_text(f"at {value['in']}", EN).hour in (value["out"], value["out"] % 12 + 12)
    for value in lists["minute_word"]["values"]:
        assert parse_time_text(f"at seven {value['in']}", EN).minute == value["out"]


@pytest.mark.parametrize(
    "text",
    ["at seven sixty", "at thirty", "at twenty four", "in five twenty minutes", "in an hundred five minutes"],
)
def test_malformed_number_words_raise(text: str) -> None:
    with pytest.raises(TimeParseError):
        parse_time_text(text, EN)


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
