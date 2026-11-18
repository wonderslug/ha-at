"""Language packs: per-language phrase tables, sentence templates and responses."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, eq=False)
class LanguagePack:
    """
    Everything language specific that the core logic needs.

    ``time_patterns`` holds regex templates with ``%(name)s`` placeholders that the
    time parser expands from the word tables below (``number``, ``unit``, ``day``,
    ``weekday``, ``period``, ``named``, ``meridiem``, plus the ``clock`` and
    ``dayref`` templates themselves). The named groups the parser reads are:
    ``count``, ``half``, ``halfonly``, ``unit``, ``named``, ``hour``, ``minute``,
    ``ampm``, ``day``, ``weekday`` and ``period``.
    """

    code: str
    time_patterns: Mapping[str, Any]
    day_words: Mapping[str, tuple[str, str | None]]  # word -> (day, implied period)
    period_words: Mapping[str, str]  # word -> morning|afternoon|evening|night
    weekday_words: Mapping[str, int]  # word -> 0 (Monday) .. 6
    unit_words: Mapping[str, int]  # word -> seconds
    number_words: Mapping[str, int]
    meridiem_words: Mapping[str, str]  # word -> am|pm
    named_times: Mapping[str, tuple[int, int]]  # word -> (hour, minute)
    sentences: Mapping[str, list[str]] = field(default_factory=dict)
    summary_verbs: Mapping[str, str] = field(default_factory=dict)  # service or verb -> template with {name}
    domain_summary_verbs: Mapping[str, str] = field(default_factory=dict)  # "intent:domain" -> template with {name}
    generic_action_summary: str = "Run action"
    joiner: str = ", "  # joins several target names, " and " in English
    domain_words: Mapping[str, str] = field(default_factory=dict)  # domain -> plural noun, "light" -> "lights"
    place_target: str = "{place}"  # an area or floor target, with {place} and {things}
    recognize_errors: Mapping[str, str] = field(default_factory=dict)  # no_match|refused|no_target[_domain]
    responses: Any = None
    logbook: Mapping[str, str] = field(default_factory=dict)  # event key -> template


def get_language_pack(language: str) -> LanguagePack | None:
    """Return the pack for a language code, or None when unsupported."""
    code = language.lower().replace("_", "-")
    if code == "en" or code.startswith("en-"):
        from .en import EN  # noqa: PLC0415

        return EN
    return None


_WEEK_DAYS = 7


def day_qualifier(pack: LanguagePack, local_due: datetime, local_now: datetime) -> str:
    """Say which day, in local time: nothing for today, then tomorrow, a weekday, or a date."""
    responses = pack.responses
    days = (local_due.date() - local_now.date()).days
    if days <= 0:
        return ""
    if days == 1:
        return str(responses["tomorrow"])
    if days < _WEEK_DAYS:
        return str(responses["weekday"]).format(weekday=responses["weekday_names"][local_due.weekday()])
    return str(responses["date"]).format(month=responses["month_names"][local_due.month - 1], day=local_due.day)
