"""Tests for the translation report builder and its renderers."""

import json
from pathlib import Path

import pytest

from tests.translations import report  # noqa: TID251  (plain module; see tests/assist.py)
from tests.translations.checks import Finding, StringsResult  # noqa: TID251  (plain module; see tests/assist.py)
from tests.translations.report import (  # noqa: TID251  (plain module; see tests/assist.py)
    build_report,
    languages_from_paths,
    main,
    render_markdown,
)


@pytest.fixture
def german_strings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Point the report at a translations folder holding English and a one-key German file."""
    (tmp_path / "en.json").write_text(json.dumps({"title": "Jobs"}), encoding="utf-8")
    (tmp_path / "de.json").write_text(json.dumps({"title": "Aufgaben"}), encoding="utf-8")
    monkeypatch.setattr(report, "TRANSLATIONS_DIR", tmp_path)


def test_en_only_paths_select_no_language() -> None:
    paths = ["custom_components/at/translations/en.json", "custom_components/at/lang/en.py"]
    assert languages_from_paths(paths) == []


def test_paths_select_languages() -> None:
    paths = [
        "custom_components/at/translations/de.json",
        "custom_components/at/lang/fr.py",
        "tests/translations/examples/fr.yaml",
        "custom_components/at/lang/__init__.py",
    ]
    assert languages_from_paths(paths) == ["de", "fr"]


@pytest.mark.usefixtures("german_strings")
def test_absent_surface() -> None:
    result = build_report(["de"])["languages"]["de"]
    assert result["voice"]["status"] == "absent"
    assert result["strings"]["status"] == "pass"
    assert result["strings"]["keys_present"] == 1


def test_unknown_language_is_absent() -> None:
    result = build_report(["xx"])["languages"]["xx"]
    assert result["strings"]["status"] == "absent"
    assert result["voice"]["status"] == "absent"


def test_examples_without_pack_fail(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "xx.yaml").write_text("now: '2026-01-01 09:00'\n", encoding="utf-8")
    monkeypatch.setattr(report, "EXAMPLES_DIR", tmp_path)
    result = build_report(["xx"])
    assert result["languages"]["xx"]["voice"]["status"] == "fail"
    assert result["languages"]["xx"]["voice"]["findings"][0]["kind"] == "no_pack"
    assert result["failed"] is True


@pytest.mark.usefixtures("german_strings")
def test_failed_reflects_any_fail(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        report,
        "check_strings",
        lambda _en, _other, language: StringsResult(language, 1, 1, [Finding("fail", "html", "a.b")]),
    )
    changed = tmp_path / "changed.txt"
    changed.write_text("custom_components/at/translations/de.json\n", encoding="utf-8")
    assert build_report(["de"])["failed"] is True
    assert main(["--changed-files", str(changed)]) == 1


def test_empty_selection_is_a_pass(tmp_path: Path) -> None:
    changed = tmp_path / "changed.txt"
    changed.write_text("custom_components/at/translations/en.json\n", encoding="utf-8")
    out = tmp_path / "report.json"
    md = tmp_path / "report.md"
    assert main(["--changed-files", str(changed), "--json", str(out), "--markdown", str(md)]) == 0
    assert json.loads(out.read_text(encoding="utf-8")) == {"failed": False, "languages": {}}
    assert md.read_text(encoding="utf-8") == ""


def test_markdown_lists_missing_keys() -> None:
    findings = [Finding("report", "missing_key", f"k.{index}") for index in range(12)]
    data = {
        "failed": False,
        "languages": {
            "de": {
                "strings": {
                    "status": "pass",
                    "keys_total": 12,
                    "keys_present": 0,
                    "findings": [vars(item) for item in findings],
                },
                "voice": {
                    "status": "absent",
                    "examples_total": 0,
                    "examples_passed": 0,
                    "categories_missing": [],
                    "findings": [],
                },
            }
        },
    }
    text = render_markdown(data)
    assert text.startswith("```text\nTranslation report — de\n")
    assert "k.9" in text
    assert "k.10" not in text
    assert "… and 2 more" in text


def test_main_writes_both_files(tmp_path: Path) -> None:
    out = tmp_path / "report.json"
    md = tmp_path / "report.md"
    assert main(["--all", "--json", str(out), "--markdown", str(md)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["failed"] is False
    assert md.exists()
