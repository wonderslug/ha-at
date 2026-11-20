"""Language packs: per-language phrase tables, sentence templates and responses."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from homeassistant.util import language as language_util


@dataclass(frozen=True, eq=False)
class LanguagePack:
    """
    Everything language specific that the core logic needs.

    ``time_patterns`` holds regex templates with ``%(name)s`` placeholders that the
    time parser expands from the word tables below (``unit``, ``day``, ``weekday``,
    ``period``, ``named``, ``meridiem``, ``scale``, ``num_<group>`` for each
    ``number_words`` group, plus the ``number``, ``clock`` and ``dayref`` templates
    themselves). The named groups the parser reads are: ``count``, ``half``,
    ``halfonly``, ``unit``, ``named``, ``hour``, ``minute``, ``hour_words``,
    ``minute_words``, ``ampm``, ``day``, ``weekday`` and ``period``, and for a time
    that is 24-hour by its wording ``hhmm``, ``hour24``, ``hour24_words`` and ``hours``.

    A number in words is read by adding up its words' values, with a ``number_scales``
    word multiplying what came before it and ``number_fillers`` words skipped; the
    ``number`` template decides which word orders are valid.
    """

    code: str
    time_patterns: Mapping[str, Any]
    day_words: Mapping[str, tuple[str, str | None]]  # word -> (day, implied period)
    period_words: Mapping[str, str]  # word -> morning|afternoon|evening|night
    weekday_words: Mapping[str, int]  # word -> 0 (Monday) .. 6
    unit_words: Mapping[str, int]  # word -> seconds
    number_words: Mapping[str, Mapping[str, int]]  # group -> word -> value
    meridiem_words: Mapping[str, str]  # word -> am|pm
    named_times: Mapping[str, tuple[int, int]]  # word -> (hour, minute)
    number_scales: Mapping[str, int] = field(default_factory=dict)  # word -> multiplier, "hundred" -> 100
    number_fillers: frozenset[str] = frozenset()  # words inside a number that add nothing, "and", "oh"
    # Sentence trigger templates by group: schedule_absolute, schedule_relative, list, cancel
    sentences: Mapping[str, list[str]] = field(default_factory=dict)
    sentence_lists: Mapping[str, Any] = field(default_factory=dict)  # hassil range/value lists the templates use
    run_pattern: str = ""  # regex with a ``name`` group for "run <automation>" outside a sentence trigger
    sentence_clock: str = ""  # a time phrase built from matched {hour}, {minute} and {meridiem}
    sentence_weekday: str = "{weekday}"  # a matched {weekday} as the time parser reads it, "on {weekday}"
    summary_verbs: Mapping[str, str] = field(default_factory=dict)  # service or verb -> template with {name}
    domain_summary_verbs: Mapping[str, str] = field(default_factory=dict)  # "intent:domain" -> template with {name}
    generic_action_summary: str = "Run action"
    joiner: str = ", "  # joins several target names, " and " in English
    domain_words: Mapping[str, str] = field(default_factory=dict)  # domain -> plural noun, "light" -> "lights"
    place_target: str = "{place}"  # an area or floor target, with {place} and {things}
    recognize_errors: Mapping[str, str] = field(default_factory=dict)  # no_match|refused|no_target[_domain]
    responses: Mapping[str, Any] = field(default_factory=dict)  # response key -> template or formatter
    logbook: Mapping[str, str] = field(default_factory=dict)  # event key -> template
    todo: Mapping[str, str] = field(default_factory=dict)  # done|failed|missed|cancelled -> description
    messages: Mapping[str, str] = field(default_factory=dict)  # error key -> template, see ``message``


def _en() -> LanguagePack:
    from .en import EN  # noqa: PLC0415 - en imports this module

    return EN


_PACKS: dict[str, Callable[[], LanguagePack]] = {"en": _en}


def language_packs() -> list[LanguagePack]:
    """Return every language pack `at` ships."""
    return [load() for load in _PACKS.values()]


def get_language_pack(language: str) -> LanguagePack | None:
    """Return the pack that best fits a language tag, as Home Assistant matches languages, or None."""
    matches = language_util.matches(language.replace("_", "-"), _PACKS)
    return _PACKS[matches[0]]() if matches else None


def message(pack: LanguagePack | None, key: str, **placeholders: object) -> str:
    """Return an error message from the pack, or the English one when the pack has none."""
    from .en import EN  # noqa: PLC0415 - en imports this module

    template = (pack.messages.get(key) if pack is not None else None) or EN.messages[key]
    return template.format(**placeholders)


_WEEK_DAYS = 7


def spoken_summary(summary: str) -> str:
    """Lowercase a summary's first letter to use it mid-sentence, unless it starts with an acronym such as "TV"."""
    if summary[:2].isalpha() and summary[:2].isupper():
        return summary
    return summary[:1].lower() + summary[1:]


def day_qualifier(pack: LanguagePack, local_due: datetime, local_now: datetime) -> str:
    """Say which day, in local time: nothing for today, then yesterday, tomorrow, a weekday, or a date."""
    responses = pack.responses
    days = (local_due.date() - local_now.date()).days
    if days == 0:
        return ""
    if days == -1:
        return str(responses["yesterday"])
    if days == 1:
        return str(responses["tomorrow"])
    if 0 < days < _WEEK_DAYS:
        return str(responses["weekday"]).format(weekday=responses["weekday_names"][local_due.weekday()])
    return str(responses["date"]).format(month=responses["month_names"][local_due.month - 1], day=local_due.day)
