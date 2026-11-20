"""
Deterministic time phrase parser.

Pure Python: no Home Assistant imports and no date libraries. Every word and
pattern comes from the ``LanguagePack``; this module contains no natural language.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, tzinfo
from functools import lru_cache
import re
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Iterable
    from zoneinfo import ZoneInfo

    from custom_components.at.lang import LanguagePack

Meridiem = Literal["am", "pm"]
Day = Literal["today", "tomorrow"]
Period = Literal["morning", "afternoon", "evening", "night"]

_PM_PERIODS = frozenset({"afternoon", "evening", "night"})
_MAX_HOUR_12 = 12
_MAX_HOUR_24 = 23
_MAX_MINUTE = 59
_DIGITS = r"\d+(?:\.\d+)?"


class TimeParseError(ValueError):
    """The text is not a time phrase this parser understands."""


@dataclass(frozen=True)
class TimeSpec:
    """A parsed, not yet resolved, time phrase."""

    relative: timedelta | None = None
    hour: int | None = None
    minute: int = 0
    meridiem: Meridiem | None = None
    day: Day | None = None
    weekday: int | None = None
    period: Period | None = None


@dataclass(frozen=True)
class ResolvedTime:
    """A time phrase resolved against a clock and time zone."""

    due: datetime
    relative: bool


def _alternation(words: Iterable[str]) -> str:
    ordered = sorted(words, key=len, reverse=True)
    return "|".join(r"\s+".join(re.escape(part) for part in w.split()) for w in ordered)


@dataclass(frozen=True)
class _Compiled:
    relative: tuple[re.Pattern[str], ...]
    phrases: tuple[re.Pattern[str], ...]
    splits: tuple[tuple[re.Pattern[str], re.Pattern[str]], ...]


@lru_cache(maxsize=8)
def _compile(pack: LanguagePack) -> _Compiled:
    tpl = pack.time_patterns
    subs = {
        **{f"num_{group}": _alternation(words) for group, words in pack.number_words.items()},
        "scale": _alternation(pack.number_scales),
        "unit": _alternation(pack.unit_words),
        "day": _alternation(pack.day_words),
        "weekday": _alternation(pack.weekday_words),
        "period": _alternation(pack.period_words),
        "named": _alternation(pack.named_times),
        "meridiem": _alternation(pack.meridiem_words),
    }
    subs["number"] = _DIGITS + "|" + tpl["number"] % subs
    subs["clock"] = tpl["clock"] % subs
    subs["dayref"] = tpl["dayref"] % subs

    def build(templates: Iterable[str]) -> tuple[re.Pattern[str], ...]:
        return tuple(re.compile(t % subs, re.IGNORECASE) for t in templates)

    relative = build(tpl["relative"])
    phrases = build(tpl["phrases"])
    splits = tuple(
        (
            re.compile(r"(?:" + p.pattern + r")(?:\s+|$)", re.IGNORECASE),
            re.compile(r"(?:^|\s+)(?:" + p.pattern + r")$", re.IGNORECASE),
        )
        for p in (*relative, *phrases)
    )
    return _Compiled(relative=relative, phrases=phrases, splits=splits)


@lru_cache(maxsize=8)
def _word_values(pack: LanguagePack) -> dict[str, int]:
    return {word: value for words in pack.number_words.values() for word, value in words.items()}


def _number(raw: str, pack: LanguagePack) -> float:
    key = raw.lower()
    if re.fullmatch(_DIGITS, key):
        return float(key)
    values = _word_values(pack)
    total = current = 0
    for word in re.split(r"[\s-]+", key):
        if word in pack.number_scales:
            total += max(current, 1) * pack.number_scales[word]
            current = 0
        elif word not in pack.number_fillers:
            current += values[word]
    return float(total + current)


def _spec_from_match(m: re.Match[str], pack: LanguagePack) -> TimeSpec:
    groups = {k: v.lower() for k, v in m.groupdict().items() if v is not None}
    if "unit" in groups or "halfonly" in groups:
        if "halfonly" in groups:
            seconds = 0.5 * pack.unit_words[groups["halfonly"]]
        else:
            count = _number(groups["count"], pack)
            if "half" in groups:
                count += 0.5
            seconds = count * pack.unit_words[groups["unit"]]
        if seconds <= 0:
            msg = "duration must be positive"
            raise TimeParseError(msg)
        return TimeSpec(relative=timedelta(seconds=seconds))

    hour: int
    minute = 0
    meridiem: Meridiem | None = None
    if "named" in groups:
        hour, minute = pack.named_times[groups["named"]]
        meridiem = "am" if hour < _MAX_HOUR_12 else "pm"
    else:
        if "hour_words" in groups:
            hour = int(_number(groups["hour_words"], pack))
            minute = int(_number(groups["minute_words"], pack)) if "minute_words" in groups else 0
        else:
            hour = int(groups["hour"])
            minute = int(groups.get("minute", "0"))
        if minute > _MAX_MINUTE:
            msg = f"invalid minute {minute}"
            raise TimeParseError(msg)
        if "ampm" in groups:
            if not 1 <= hour <= _MAX_HOUR_12:
                msg = f"invalid hour {hour}"
                raise TimeParseError(msg)
            meridiem = pack.meridiem_words[groups["ampm"]]  # type: ignore[assignment]
            hour = hour % 12 + (12 if meridiem == "pm" else 0)
        elif hour > _MAX_HOUR_24:
            msg = f"invalid hour {hour}"
            raise TimeParseError(msg)
        elif hour > _MAX_HOUR_12:
            meridiem = "pm"
        elif hour == 0:
            hour, meridiem = 0, "am"

    day: Day | None = None
    period: Period | None = None
    weekday: int | None = None
    if "day" in groups:
        day_name, implied = pack.day_words[groups["day"]]
        day = day_name  # type: ignore[assignment]
        period = implied  # type: ignore[assignment]
    if "weekday" in groups:
        weekday = pack.weekday_words[groups["weekday"]]
    if "period" in groups:
        period = pack.period_words[groups["period"]]  # type: ignore[assignment]
    return TimeSpec(hour=hour, minute=minute, meridiem=meridiem, day=day, weekday=weekday, period=period)


def _clean(text: str) -> str:
    return text.strip().rstrip(".,!?;: ").strip()


def parse_time_text(text: str, pack: LanguagePack) -> TimeSpec:
    """Parse a whole string that is just a time phrase."""
    cleaned = _clean(text)
    compiled = _compile(pack)
    for pattern in (*compiled.relative, *compiled.phrases):
        m = pattern.fullmatch(cleaned)
        if m:
            return _spec_from_match(m, pack)
    msg = f"not a time phrase: {text!r}"
    raise TimeParseError(msg)


def split_time_and_command(text: str, pack: LanguagePack) -> tuple[TimeSpec, str]:
    """Split a sentence into its time phrase (at the start or end) and the rest."""
    cleaned = _clean(text)
    best: tuple[int, re.Match[str], str] | None = None
    for starts, ends in _compile(pack).splits:
        for rx, where in ((starts, "start"), (ends, "end")):
            m = rx.match(cleaned) if where == "start" else rx.search(cleaned)
            if m is None:
                continue
            command = (cleaned[m.end() :] if where == "start" else cleaned[: m.start()]).strip()
            span = m.end() - m.start()
            if best is None or span > best[0]:
                best = (span, m, command)
    if best is None:
        msg = f"no time phrase at the start or end of {text!r}"
        raise TimeParseError(msg)
    return _spec_from_match(best[1], pack), best[2]


def _wall_to_aware(d: date, hour: int, minute: int, tz: ZoneInfo) -> datetime:
    """Build a local time; a non-existent one moves forward to the first valid minute."""
    return _first_valid(datetime(d.year, d.month, d.day, hour, minute), tz)


def _first_valid(naive: datetime, tz: tzinfo) -> datetime:
    for _ in range(24 * 60):
        local = naive.replace(tzinfo=tz, fold=0)
        if local.astimezone(UTC).astimezone(tz).replace(tzinfo=None) == naive:
            return local
        naive = (naive + timedelta(minutes=1)).replace(second=0, microsecond=0)
    return naive.replace(tzinfo=tz, fold=0)  # pragma: no cover


def wall_time_to_utc(naive: datetime, tz: tzinfo) -> datetime:
    """
    Read a naive wall-clock time in ``tz`` with the parser's rules, as an aware UTC instant.

    A time in a spring-forward gap moves to the first valid minute after it; a repeated
    fall-back time is the first of the two.
    """
    return _first_valid(naive, tz).astimezone(UTC)


def candidate_hours(spec: TimeSpec) -> list[int]:
    """Return the 24-hour readings of a clock time: one with a meridiem or period, otherwise both."""
    hour = spec.hour
    if hour is None:
        msg = "no time of day"
        raise TimeParseError(msg)
    if spec.meridiem is not None:
        return [hour]
    if spec.period is not None:
        return [hour % 12 + (12 if spec.period in _PM_PERIODS else 0)]
    return sorted({hour % 12, hour % 12 + 12})


def resolve(spec: TimeSpec, now: datetime, tz: ZoneInfo) -> ResolvedTime:
    """Resolve a spec to an aware UTC instant relative to ``now``."""
    if spec.relative is not None:
        return ResolvedTime(due=now.astimezone(UTC) + spec.relative, relative=True)

    hours = candidate_hours(spec)
    local_now = now.astimezone(tz)
    today = local_now.date()

    def candidates(offset: int) -> list[datetime]:
        d = today + timedelta(days=offset)
        return [_wall_to_aware(d, h, spec.minute, tz) for h in hours]

    def first_after(offset: int) -> datetime | None:
        later = [c for c in candidates(offset) if c.astimezone(UTC) > now.astimezone(UTC)]
        return min(later, key=lambda c: c.astimezone(UTC)) if later else None

    if spec.weekday is not None:
        offset = (spec.weekday - today.weekday()) % 7
        chosen = first_after(offset) or first_after(offset + 7)
    elif spec.day == "tomorrow":
        chosen = first_after(1)
    else:
        chosen = first_after(0) or first_after(1)
    if chosen is None:  # pragma: no cover
        msg = "could not resolve time"
        raise TimeParseError(msg)
    return ResolvedTime(due=chosen.astimezone(UTC), relative=False)
