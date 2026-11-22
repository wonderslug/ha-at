"""Checks that every translation of the integration must pass, shared by the tests and the CI report."""

from collections.abc import Mapping
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Any, Literal

Severity = Literal["fail", "report"]

TRANSLATIONS_DIR = Path(__file__).resolve().parents[2] / "custom_components" / "at" / "translations"

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
            language, len(en_leaves), 0, [Finding("fail", "unknown_key", "", "The file root is not a JSON object.")]
        )

    translated = _flatten(other)
    findings: list[Finding] = []
    present = 0

    for key, value in translated.items():
        if key not in en_leaves:
            findings.append(Finding("fail", "unknown_key", key, "The key does not exist in English."))
        elif not isinstance(value, str):
            findings.append(Finding("fail", "unknown_key", key, "The value is not a string."))

    for key, english_value in en_leaves.items():
        value = translated.get(key)
        if not isinstance(value, str):
            if key not in translated:
                findings.append(Finding("report", "missing_key", key))
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
