"""Checks that every translation of the integration must pass, shared by the tests and the CI report."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, fields
from datetime import datetime
import json
from pathlib import Path
import re
import string
from typing import Any, Literal
from zoneinfo import ZoneInfo

from custom_components.at.core.timeparse import TimeParseError, parse_time_text, resolve
from custom_components.at.ha_internal.sentence_triggers import (
    LanguageSentences,
    SentenceGroup,
    TriggerInput,
    _parser,
    match_sentence,
)
from custom_components.at.lang import LanguagePack
from custom_components.at.voice.triggers import sentence_groups

Severity = Literal["fail", "report"]

TRANSLATIONS_DIR = Path(__file__).resolve().parents[2] / "custom_components" / "at" / "translations"

EXAMPLES_DIR = Path(__file__).resolve().parent / "examples"

TIME_CATEGORIES = ("relative", "clock", "day", "weekday", "named", "spelled_number")
SENTENCE_GROUPS = ("schedule", "list", "cancel", "run", "announce")

MAIN_SUITE_FATAL = frozenset(
    {"html", "url", "whitespace", "empty", "not_string", "not_object", "no_examples", "no_pack", "bad_examples"}
)

_TIME_FORMAT = "%Y-%m-%d %H:%M"
_DEFAULT_TIME_ZONE = "America/Chicago"

_PLACEHOLDER = re.compile(r"\{(\w+)\}")
_HTML = re.compile(r"<[a-zA-Z/]")
_URL = re.compile(r"https?://")


@dataclass(frozen=True)
class Finding:
    """One problem or observation about a translation."""

    severity: Severity
    kind: str
    key: str
    detail: str = ""


def fatal_in_main_suite(findings: Iterable[Finding]) -> list[Finding]:
    """Return the findings that fail the main test suite.

    Key and placeholder drift against English, and example mismatches, fail only the translation workflow for the
    language a pull request touches, so an English change never turns the suite red because another language lags.
    """
    return [finding for finding in findings if finding.severity == "fail" and finding.kind in MAIN_SUITE_FATAL]


@dataclass
class StringsResult:
    """Outcome of checking one translation file against English."""

    language: str
    keys_total: int
    keys_present: int
    findings: list[Finding] = field(default_factory=list)


def load_json(path: Path) -> Any:
    """Read a JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def translation_languages() -> list[str]:
    """Return the language codes of every translation file except English."""
    return sorted(path.stem for path in TRANSLATIONS_DIR.glob("*.json") if path.stem != "en")


def _flatten(tree: Any, prefix: str = "") -> dict[str, Any]:
    """Map dotted paths to the leaves of a nested mapping."""
    leaves: dict[str, Any] = {}
    for name, value in tree.items():
        path = f"{prefix}.{name}" if prefix else str(name)
        if isinstance(value, Mapping):
            leaves.update(_flatten(value, path))
        else:
            leaves[path] = value
    return leaves


def check_strings(english: Mapping[str, Any], other: Any, language: str) -> StringsResult:
    """Compare a translation with English; hard problems fail, gaps are only reported."""
    en_leaves = {key: value for key, value in _flatten(english).items() if isinstance(value, str)}
    if not isinstance(other, Mapping):
        return StringsResult(
            language, len(en_leaves), 0, [Finding("fail", "not_object", "", "The file root is not a JSON object.")]
        )

    translated = _flatten(other)
    findings: list[Finding] = []
    present = 0

    for key, value in translated.items():
        if key not in en_leaves:
            findings.append(Finding("fail", "unknown_key", key, "The key does not exist in English."))
        elif not isinstance(value, str):
            findings.append(Finding("fail", "not_string", key, "The value is not a string."))

    for key, english_value in en_leaves.items():
        value = translated.get(key)
        if not isinstance(value, str):
            if key not in translated:
                findings.append(Finding("report", "missing_key", key))
            continue
        if not value.strip():
            findings.append(Finding("fail", "empty", key))
            continue
        present += 1
        if set(_PLACEHOLDER.findall(value)) != set(_PLACEHOLDER.findall(english_value)):
            findings.append(Finding("fail", "placeholders", key, f"English: {english_value!r}"))
        if _HTML.search(value):
            findings.append(Finding("fail", "html", key))
        if value != value.strip():
            findings.append(Finding("fail", "whitespace", key))
        if _URL.search(value):
            findings.append(Finding("fail", "url", key))
        if value == english_value:
            findings.append(Finding("report", "identical", key))

    return StringsResult(language, len(en_leaves), present, findings)


@dataclass
class PackResult:
    """Outcome of checking one voice pack against its examples."""

    language: str
    examples_total: int
    examples_passed: int
    categories_missing: list[str]
    findings: list[Finding] = field(default_factory=list)


async def _no_answer(_given: TriggerInput) -> str:
    return ""


def _template_fields(template: str) -> set[str]:
    try:
        return {name for _, name, _, _ in string.Formatter().parse(template) if name}
    except ValueError:
        return {"<unparsable>"}


def _check_templates(pack: LanguagePack, english: LanguagePack) -> list[Finding]:
    findings: list[Finding] = []
    skipped = {"code", "time_patterns", "sentences", "sentence_lists"}
    for item in fields(LanguagePack):
        if item.name in skipped:
            continue
        en_value = getattr(english, item.name)
        value = getattr(pack, item.name)
        if isinstance(en_value, str):
            pairs = [(item.name, en_value, value)]
        elif isinstance(en_value, Mapping) and isinstance(value, Mapping):
            pairs = [(f"{item.name}.{key}", text, value.get(key)) for key, text in en_value.items()]
        else:
            continue
        for key, en_text, text in pairs:
            if not isinstance(en_text, str) or not isinstance(text, str):
                continue
            if _template_fields(text) != _template_fields(en_text):
                findings.append(Finding("fail", "template_placeholders", key, f"English: {en_text!r}"))
    return findings


def _bad(index: int, section: str, problem: str) -> Finding:
    return Finding("fail", "bad_examples", f"{section}[{index}]", problem)


def _check_time(
    index: int, entry: Any, pack: LanguagePack, now: datetime, tz: ZoneInfo
) -> tuple[Finding | None, str | None, bool]:
    """Return a finding, the category covered, and whether the example passed."""
    if not isinstance(entry, Mapping) or not isinstance(entry.get("text"), str) or "expect" not in entry:
        return _bad(index, "times", "Needs text, category and expect."), None, False
    category = entry.get("category")
    if category not in TIME_CATEGORIES:
        return _bad(index, "times", f"Unknown category {category!r}."), None, False
    expect = entry["expect"]
    if expect is not None and not isinstance(expect, str):
        return _bad(index, "times", "expect must be a date string or null."), None, False
    text = entry["text"]
    try:
        got: str | None = resolve(parse_time_text(text, pack), now, tz).due.astimezone(tz).strftime(_TIME_FORMAT)
    except TimeParseError:
        got = None
    if got == expect:
        return None, category, True
    return Finding("fail", "time_example", text, f"Got {got!r}, expected {expect!r}."), category, False


def _check_sentence(
    index: int, entry: Any, language: LanguageSentences, parser: Any
) -> tuple[Finding | None, str | None, bool]:
    if not isinstance(entry, Mapping) or not isinstance(entry.get("text"), str):
        return _bad(index, "sentences", "Needs text and group."), None, False
    group = entry.get("group")
    slots = entry.get("slots", {})
    if group not in SENTENCE_GROUPS:
        return _bad(index, "sentences", f"Unknown group {group!r}."), None, False
    if not isinstance(slots, Mapping):
        return _bad(index, "sentences", "slots must be a mapping."), None, False
    text = entry["text"]
    match = match_sentence(language, text, parser)
    if match is None:
        return Finding("fail", "sentence_example", text, f"No group matched, expected {group!r}."), group, False
    if match.group.name != group:
        return (
            Finding("fail", "sentence_example", text, f"Got group {match.group.name!r}, expected {group!r}."),
            group,
            False,
        )
    for name, value in slots.items():
        if match.wildcards.get(name) != str(value):
            return (
                Finding(
                    "fail",
                    "sentence_example",
                    text,
                    f"Slot {name!r} was {match.wildcards.get(name)!r}, expected {value!r}.",
                ),
                group,
                False,
            )
    return None, group, True


def check_pack(pack: LanguagePack, examples: Mapping[str, Any] | None, english: LanguagePack) -> PackResult:
    """Check a voice pack's templates and run its examples through the real parser and matcher."""
    findings = _check_templates(pack, english)
    for key, en_sentences in english.sentences.items():
        if en_sentences and not pack.sentences.get(key):
            findings.append(Finding("report", "empty_group", key))

    if examples is None:
        findings.append(Finding("fail", "no_examples", "", "No examples file for this language."))
        return PackResult(pack.code, 0, 0, [*TIME_CATEGORIES, *SENTENCE_GROUPS], findings)

    try:
        tz = ZoneInfo(str(examples.get("time_zone", _DEFAULT_TIME_ZONE)))
        now = datetime.strptime(str(examples["now"]), _TIME_FORMAT).replace(tzinfo=tz)
        times = examples.get("times") or []
        sentences = examples.get("sentences") or []
    except (KeyError, ValueError, TypeError, AttributeError, OSError) as err:
        findings.append(Finding("fail", "bad_examples", "", f"Unreadable header: {err}"))
        return PackResult(pack.code, 0, 0, [*TIME_CATEGORIES, *SENTENCE_GROUPS], findings)
    if not isinstance(times, list) or not isinstance(sentences, list):
        findings.append(Finding("fail", "bad_examples", "", "times and sentences must be lists."))
        return PackResult(pack.code, 0, 0, [*TIME_CATEGORIES, *SENTENCE_GROUPS], findings)

    language = LanguageSentences(
        pack.code,
        [SentenceGroup(name, templates, _no_answer) for name, templates in sentence_groups(pack, defer_relative=False)],
        pack.sentence_lists,
        _no_answer,
    )
    parser = _parser(language)

    covered: set[str] = set()
    total = passed = 0
    for index, entry in enumerate(times):
        finding, category, ok = _check_time(index, entry, pack, now, tz)
        total += finding is None or finding.kind != "bad_examples"
        passed += ok
        if category:
            covered.add(category)
        if finding:
            findings.append(finding)
    for index, entry in enumerate(sentences):
        finding, group, ok = _check_sentence(index, entry, language, parser)
        total += finding is None or finding.kind != "bad_examples"
        passed += ok
        if group:
            covered.add(group)
        if finding:
            findings.append(finding)

    missing = [name for name in (*TIME_CATEGORIES, *SENTENCE_GROUPS) if name not in covered]
    findings.extend(Finding("report", "missing_category", name) for name in missing)
    return PackResult(pack.code, total, passed, missing, findings)
