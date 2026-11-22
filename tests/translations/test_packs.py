"""Tests for the voice-pack checks."""

from dataclasses import replace
from typing import Any

import pytest
import yaml

from custom_components.at.lang import _PACKS
from custom_components.at.lang.en import EN
from tests.translations.checks import (  # noqa: TID251  (plain module; see tests/assist.py)
    EXAMPLES_DIR,
    PackResult,
    check_pack,
)

NOW = "2026-11-17 22:22"


def _examples(times: list[dict[str, Any]] | None = None, sentences: list[dict[str, Any]] | None = None) -> dict:
    return {"language": "en", "now": NOW, "times": times or [], "sentences": sentences or []}


def _failures(result: PackResult) -> list[tuple[str, str]]:
    return [(f.kind, f.key) for f in result.findings if f.severity == "fail"]


def test_english_examples_all_pass() -> None:
    examples = yaml.safe_load((EXAMPLES_DIR / "en.yaml").read_text(encoding="utf-8"))
    result = check_pack(EN, examples, EN)
    assert _failures(result) == []
    assert result.examples_total > 0
    assert result.examples_passed == result.examples_total
    assert result.categories_missing == []


def test_missing_examples_file_fails() -> None:
    assert _failures(check_pack(EN, None, EN)) == [("no_examples", "")]


def test_wrong_time_expectation_fails() -> None:
    result = check_pack(
        EN, _examples([{"category": "relative", "text": "in 20 minutes", "expect": "2026-11-17 22:43"}]), EN
    )
    assert _failures(result) == [("time_example", "in 20 minutes")]
    detail = next(f.detail for f in result.findings if f.kind == "time_example")
    assert "2026-11-17 22:42" in detail
    assert "2026-11-17 22:43" in detail
    assert result.examples_passed == 0


def test_expected_unparseable_that_parses_fails() -> None:
    result = check_pack(EN, _examples([{"category": "relative", "text": "in 20 minutes", "expect": None}]), EN)
    assert _failures(result) == [("time_example", "in 20 minutes")]


def test_expected_unparseable_passes() -> None:
    result = check_pack(EN, _examples([{"category": "clock", "text": "in the purple moon", "expect": None}]), EN)
    assert _failures(result) == []
    assert result.examples_passed == 1


def test_sentence_in_wrong_group_fails() -> None:
    result = check_pack(EN, _examples(sentences=[{"text": "run the morning routine", "group": "schedule"}]), EN)
    assert _failures(result) == [("sentence_example", "run the morning routine")]


def test_slot_mismatch_fails() -> None:
    sentence = {"text": "run the morning routine", "group": "run", "slots": {"name": "x"}}
    result = check_pack(EN, _examples(sentences=[sentence]), EN)
    assert _failures(result) == [("sentence_example", "run the morning routine")]


def test_missing_category_is_reported() -> None:
    times = [{"category": "relative", "text": "in 20 minutes", "expect": "2026-11-17 22:42"}]
    result = check_pack(EN, _examples(times), EN)
    assert "weekday" in result.categories_missing
    assert "relative" not in result.categories_missing
    assert ("report", "missing_category", "weekday") in [(f.severity, f.kind, f.key) for f in result.findings]


def test_template_placeholder_change_fails() -> None:
    key = next(k for k, v in EN.responses.items() if isinstance(v, str) and "{" in v)
    pack = replace(EN, responses={**EN.responses, key: "no fields"})
    result = check_pack(pack, _examples(), EN)
    assert ("template_placeholders", f"responses.{key}") in _failures(result)


def test_empty_group_is_reported() -> None:
    pack = replace(EN, sentences={**EN.sentences, "run": []})
    result = check_pack(pack, _examples(), EN)
    assert ("report", "empty_group", "run") in [(f.severity, f.kind, f.key) for f in result.findings]


def test_malformed_examples_fail() -> None:
    result = check_pack(EN, {"times": [{"text": "x"}]}, EN)
    assert [kind for kind, _ in _failures(result)] == ["bad_examples"]


@pytest.mark.parametrize("code", list(_PACKS))
def test_registered_pack(code: str) -> None:
    path = EXAMPLES_DIR / f"{code}.yaml"
    examples = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else None
    pack = _PACKS[code]()
    assert _failures(check_pack(pack, examples, EN)) == []
