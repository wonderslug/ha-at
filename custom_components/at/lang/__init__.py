"""Language packs: per-language phrase tables, sentence templates and responses."""

from collections.abc import Mapping
from dataclasses import dataclass, field
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
    responses: Any = None


def get_language_pack(language: str) -> LanguagePack | None:
    """Return the pack for a language code, or None when unsupported."""
    code = language.lower().replace("_", "-")
    if code == "en" or code.startswith("en-"):
        from .en import EN  # noqa: PLC0415

        return EN
    return None
