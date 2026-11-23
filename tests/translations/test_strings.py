"""Tests for the translated-string checks."""

import pytest

from tests.translations.checks import (  # noqa: TID251  (plain module; see tests/assist.py)
    MAIN_SUITE_FATAL,
    TRANSLATIONS_DIR,
    check_strings,
    fatal_in_main_suite,
    load_json,
    translation_languages,
)

EN = {"config": {"step": {"user": {"title": "Set up {name}", "data": {"x": "Delay"}}}}}


def _de(title: str = "Einrichten {name}", x: str = "Verzögerung") -> dict:
    return {"config": {"step": {"user": {"title": title, "data": {"x": x}}}}}


def _kinds(result, severity: str) -> list[tuple[str, str]]:
    return [(f.kind, f.key) for f in result.findings if f.severity == severity]


def test_complete_translation_has_no_findings() -> None:
    result = check_strings(EN, _de(), "de")
    assert result.keys_total == result.keys_present == 2
    assert result.findings == []


def test_unknown_key_fails() -> None:
    other = _de()
    other["config"]["step"]["user"]["bogus"] = "x"
    result = check_strings(EN, other, "de")
    assert _kinds(result, "fail") == [("unknown_key", "config.step.user.bogus")]


def test_changed_placeholder_fails() -> None:
    result = check_strings(EN, _de(title="Einrichten {nom}"), "de")
    assert _kinds(result, "fail") == [("placeholders", "config.step.user.title")]


def test_dropped_placeholder_fails() -> None:
    result = check_strings(EN, _de(title="Einrichten"), "de")
    assert _kinds(result, "fail") == [("placeholders", "config.step.user.title")]


def test_html_fails() -> None:
    result = check_strings(EN, _de(x="<b>Verzögerung</b>"), "de")
    assert _kinds(result, "fail") == [("html", "config.step.user.data.x")]


def test_leading_or_trailing_space_fails() -> None:
    for value in (" Verzögerung", "Verzögerung "):
        result = check_strings(EN, _de(x=value), "de")
        assert _kinds(result, "fail") == [("whitespace", "config.step.user.data.x")]


def test_url_fails() -> None:
    result = check_strings(EN, _de(x="see https://x.y"), "de")
    assert _kinds(result, "fail") == [("url", "config.step.user.data.x")]


def test_missing_key_is_reported_not_failed() -> None:
    other = {"config": {"step": {"user": {"title": "Einrichten {name}"}}}}
    result = check_strings(EN, other, "de")
    assert _kinds(result, "fail") == []
    assert _kinds(result, "report") == [("missing_key", "config.step.user.data.x")]
    assert result.keys_present == 1


def test_identical_to_english_is_reported() -> None:
    result = check_strings(EN, _de(x="Delay"), "de")
    assert _kinds(result, "fail") == []
    assert _kinds(result, "report") == [("identical", "config.step.user.data.x")]


def test_non_string_value_fails() -> None:
    result = check_strings(EN, _de(x=5), "de")  # type: ignore[arg-type]
    assert _kinds(result, "fail") == [("not_string", "config.step.user.data.x")]


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_value_fails(value: str) -> None:
    result = check_strings(EN, _de(x=value), "de")
    assert _kinds(result, "fail") == [("empty", "config.step.user.data.x")]
    assert result.keys_present == 1


def test_main_suite_ignores_gaps_that_only_the_translation_workflow_fails() -> None:
    other = _de(title="Einrichten {other}")
    other["config"]["step"]["user"]["bogus"] = "x"
    result = check_strings(EN, other, "de")
    assert {f.kind for f in result.findings if f.severity == "fail"} == {"unknown_key", "placeholders"}
    assert fatal_in_main_suite(result.findings) == []
    assert [f.kind for f in fatal_in_main_suite(check_strings(EN, _de(x="<b>x</b>"), "de").findings)] == ["html"]


def test_fatal_kinds_cover_the_value_rules() -> None:
    assert {"html", "url", "whitespace", "empty", "not_string", "not_object"} <= MAIN_SUITE_FATAL
    assert not {"unknown_key", "placeholders", "template_placeholders", "time_example", "sentence_example"} & (
        MAIN_SUITE_FATAL
    )


def test_non_object_json_root_fails() -> None:
    result = check_strings(EN, [], "de")
    assert [(f.severity, f.kind, f.key) for f in result.findings] == [("fail", "not_object", "")]
    assert result.keys_present == 0


@pytest.mark.parametrize("language", translation_languages() or [pytest.param("none", marks=pytest.mark.skip)])
def test_translation_file(language: str) -> None:
    result = check_strings(
        load_json(TRANSLATIONS_DIR / "en.json"), load_json(TRANSLATIONS_DIR / f"{language}.json"), language
    )
    assert fatal_in_main_suite(result.findings) == []
