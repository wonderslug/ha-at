"""Build the translation report CI posts on a pull request, as JSON for the triage script and as Markdown."""

import argparse
from collections.abc import Iterable, Sequence
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any

import yaml

from custom_components.at.lang import _PACKS, get_language_pack
from custom_components.at.lang.en import EN
from tests.translations.checks import (  # noqa: TID251  (plain module; see tests/assist.py)
    EXAMPLES_DIR,
    TRANSLATIONS_DIR,
    Finding,
    check_pack,
    check_strings,
    load_json,
    translation_languages,
)

_SURFACE_PATTERNS = (
    ("custom_components/at/translations/", ".json"),
    ("custom_components/at/lang/", ".py"),
    ("tests/translations/examples/", ".yaml"),
)
_LIST_LIMIT = 10


def languages_from_paths(paths: Iterable[str]) -> list[str]:
    """Return the sorted language codes that changed paths belong to, English excluded."""
    codes: set[str] = set()
    for path in paths:
        for prefix, suffix in _SURFACE_PATTERNS:
            if path.startswith(prefix) and path.endswith(suffix):
                code = path[len(prefix) : -len(suffix)]
                if "/" not in code and code not in {"en", "__init__"}:
                    codes.add(code)
    return sorted(codes)


def _status(findings: Sequence[Finding]) -> str:
    return "fail" if any(item.severity == "fail" for item in findings) else "pass"


def _unreadable(err: Exception) -> list[dict[str, Any]]:
    return [asdict(Finding("fail", "unreadable", "", str(err)))]


def _strings_section(code: str) -> dict[str, Any]:
    path = TRANSLATIONS_DIR / f"{code}.json"
    if not path.exists():
        return {"status": "absent", "keys_total": 0, "keys_present": 0, "findings": []}
    english = load_json(TRANSLATIONS_DIR / "en.json")
    try:
        other = load_json(path)
    except (ValueError, UnicodeDecodeError) as err:
        return {"status": "fail", "keys_total": 0, "keys_present": 0, "findings": _unreadable(err)}
    result = check_strings(english, other, code)
    return {
        "status": _status(result.findings),
        "keys_total": result.keys_total,
        "keys_present": result.keys_present,
        "findings": [asdict(item) for item in result.findings],
    }


def _voice_section(code: str) -> dict[str, Any]:
    examples_path = EXAMPLES_DIR / f"{code}.yaml"
    pack = get_language_pack(code) if code in _PACKS else None
    if pack is None:
        if not examples_path.exists():
            return {
                "status": "absent",
                "examples_total": 0,
                "examples_passed": 0,
                "categories_missing": [],
                "findings": [],
            }
        findings = [Finding("fail", "no_pack", "", "An examples file exists but no language pack is registered.")]
        return {
            "status": "fail",
            "examples_total": 0,
            "examples_passed": 0,
            "categories_missing": [],
            "findings": [asdict(item) for item in findings],
        }
    try:
        examples = yaml.safe_load(examples_path.read_text(encoding="utf-8")) if examples_path.exists() else None
    except (yaml.YAMLError, UnicodeDecodeError) as err:
        return {
            "status": "fail",
            "examples_total": 0,
            "examples_passed": 0,
            "categories_missing": [],
            "findings": _unreadable(err),
        }
    result = check_pack(pack, examples, EN)
    return {
        "status": _status(result.findings),
        "examples_total": result.examples_total,
        "examples_passed": result.examples_passed,
        "categories_missing": list(result.categories_missing),
        "findings": [asdict(item) for item in result.findings],
    }


def build_report(languages: Sequence[str]) -> dict[str, Any]:
    """Run every check for the given languages and return the report structure."""
    report: dict[str, Any] = {"failed": False, "languages": {}}
    for code in languages:
        entry = {"strings": _strings_section(code), "voice": _voice_section(code)}
        report["languages"][code] = entry
        if "fail" in (entry["strings"]["status"], entry["voice"]["status"]):
            report["failed"] = True
    return report


def _keys(findings: Sequence[dict[str, Any]], kind: str) -> list[str]:
    return [item["key"] for item in findings if item["kind"] == kind]


def _listed(keys: Sequence[str]) -> str:
    shown = ", ".join(keys[:_LIST_LIMIT])
    extra = len(keys) - _LIST_LIMIT
    return f"{shown}, … and {extra} more" if extra > 0 else shown


def _strings_lines(strings: dict[str, Any]) -> list[str]:
    if strings["status"] == "absent":
        return ["  Strings + panel   no translation file"]
    findings = strings["findings"]
    lines = [f"  Strings + panel   {strings['keys_present']}/{strings['keys_total']} keys"]
    missing = _keys(findings, "missing_key")
    if missing:
        lines[0] += f"   {len(missing)} missing: {_listed(missing)}"
    problems = [item for item in findings if item["severity"] == "fail"]
    changed = _keys(findings, "placeholders")
    lines.append(
        f"  Placeholders      {len(changed)} changed: {_listed(changed)}" if changed else "  Placeholders      all kept"
    )
    lines.extend(
        f"  Problem           {item['kind']}: {item['key']} {item['detail']}".rstrip()
        for item in problems
        if item["kind"] != "placeholders"
    )
    identical = _keys(findings, "identical")
    if identical:
        lines.append(f"  Untranslated      {len(identical)} identical to English: {_listed(identical)}")
    else:
        lines.append("  Untranslated      none identical to English")
    return lines


def _voice_lines(voice: dict[str, Any]) -> list[str]:
    if voice["status"] == "absent":
        return ["  Voice pack        none"]
    total = len(voice["categories_missing"])
    line = f"  Voice pack        {voice['examples_passed']}/{voice['examples_total']} examples pass"
    if total:
        line += f" · missing categories: {_listed(voice['categories_missing'])}"
    lines = [line]
    lines.extend(
        f"  Problem           {item['kind']}: {item['key']} {item['detail']}".rstrip()
        for item in voice["findings"]
        if item["severity"] == "fail"
    )
    empty = _keys(voice["findings"], "empty_group")
    if empty:
        lines.append(f"  Empty groups      {_listed(empty)}")
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    """Render one fenced text block per language, without the review line the triage script adds."""
    blocks: list[str] = []
    for code in sorted(report["languages"]):
        entry = report["languages"][code]
        lines = [f"Translation report — {code}", *_strings_lines(entry["strings"]), *_voice_lines(entry["voice"])]
        blocks.append("```text\n" + "\n".join(lines) + "\n```")
    return "\n\n".join(blocks) + "\n" if blocks else ""


def main(argv: list[str] | None = None) -> int:
    """Run the report; return 1 when any check failed."""
    parser = argparse.ArgumentParser(description="Report on the translations of the integration.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--changed-files", type=Path, help="File listing changed paths, one per line.")
    source.add_argument("--all", action="store_true", help="Report on every translated language.")
    parser.add_argument("--json", type=Path, help="Write the JSON report here.")
    parser.add_argument("--markdown", type=Path, help="Write the Markdown report here.")
    args = parser.parse_args(argv)

    if args.all:
        languages = sorted({*translation_languages(), *(path.stem for path in EXAMPLES_DIR.glob("*.yaml"))} - {"en"})
    else:
        languages = languages_from_paths(args.changed_files.read_text(encoding="utf-8").splitlines())

    report = build_report(languages)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(report), encoding="utf-8")
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
