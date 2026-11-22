#!/usr/bin/env python3
"""Decide translation labels and the sticky report comment for a pull request.

Runs in a privileged workflow on the default branch's code only. Everything read from the report artifact or from the
pull request is untrusted: it is validated, size-capped and never passed through a shell. Standard library and PyYAML
only.

Usage:
    translation_triage.py run --artifact DIR --run-head-sha SHA --run-conclusion CONCLUSION
    translation_triage.py daily
"""

import argparse
import base64
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
from urllib.parse import quote

import yaml

WAIT_DAYS = 30
MARKER = "<!-- at-translation-report -->"
STATE_PREFIX = "<!-- at-translation-state "
BASE = "translation"
NEEDS_REVIEW = "translation: needs native review"
VERIFIED = "translation: verified"
UNVERIFIED = "translation: unverified"
BOT_LOGIN = "github-actions[bot]"
COMMENT_LIMIT = 60_000
MAX_LANGUAGES = 100
MAX_LISTED_MAINTAINERS = 10
BEYOND_NOTE = "This pull request also changes code beyond translations — confirm by hand."
MAINTAINERS_PATH = ".github/translation-maintainers.yml"

_SHA = re.compile(r"[0-9a-f]{40}")
_CODE = re.compile(r"[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*")
_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
_STATE_LINE = re.compile(r"^<!-- at-translation-state (\{.*\}) -->$", re.MULTILINE)
_REVIEW_HEADING = "\n### Review\n"
_SURFACES = (
    re.compile(r"custom_components/at/translations/([^/]+)\.json"),
    re.compile(r"custom_components/at/lang/([^/]+)\.py"),
    re.compile(r"tests/translations/examples/([^/]+)\.yaml"),
)
_ENGLISH_STRINGS = "custom_components/at/translations/en.json"
_MAX_ARTIFACT_BYTES = 1_000_000
_COUNTED_STATES = {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}


@dataclass(frozen=True)
class Review:
    """One pull request review."""

    login: str
    state: str
    submitted_at: datetime
    commit_id: str


@dataclass
class Decision:
    """Labels to change and the comment to post."""

    add: set[str]
    remove: set[str]
    comment: str
    post_unverified_notice: bool


def latest_reviews(reviews: Iterable[Review]) -> dict[str, Review]:
    """Return each reviewer's latest approving or blocking review, keyed by lower-case login."""
    latest: dict[str, Review] = {}
    for item in reviews:
        if item.state not in _COUNTED_STATES:
            continue
        key = item.login.lower()
        if key not in latest or item.submitted_at >= latest[key].submitted_at:
            latest[key] = item
    return latest


def _approvers(reviews: Iterable[Review], author: str, head_sha: str | None) -> list[str]:
    return [
        key
        for key, item in latest_reviews(reviews).items()
        if item.state == "APPROVED" and key != author.lower() and (head_sha is None or item.commit_id == head_sha)
    ]


def _listed(maintainers: Mapping[str, list[str]], language: str) -> set[str]:
    return {login.lower() for login in maintainers.get(language.lower(), [])}


def qualifying_approvers(
    reviews: Iterable[Review],
    author: str,
    language: str,
    maintainers: Mapping[str, list[str]],
    head_sha: str | None = None,
) -> list[str]:
    """Return listed maintainers whose latest review approves the current head and who are not the author."""
    listed = _listed(maintainers, language)
    return sorted(login for login in _approvers(reviews, author, head_sha) if login in listed)


def other_approvers(
    reviews: Iterable[Review],
    author: str,
    language: str,
    maintainers: Mapping[str, list[str]],
    head_sha: str | None = None,
) -> list[str]:
    """Return approvers who are not listed maintainers for the language."""
    listed = _listed(maintainers, language)
    return sorted(login for login in _approvers(reviews, author, head_sha) if login not in listed)


def waiting_day(applied_at: datetime | None, now: datetime) -> int | None:
    """Return whole days since the needs-review label was applied, or None when it was not."""
    if applied_at is None:
        return None
    return max((now - applied_at).days, 0)


def validate_report(report: Any) -> dict[str, Any] | None:
    """Return the report when it has the expected shape, else None."""
    if not isinstance(report, dict) or not isinstance(report.get("failed"), bool):
        return None
    languages = report.get("languages")
    if not isinstance(languages, dict) or len(languages) > MAX_LANGUAGES:
        return None
    for code, entry in languages.items():
        if not isinstance(code, str) or not _CODE.fullmatch(code) or not isinstance(entry, dict):
            return None
    return report


def _sanitise_markdown(markdown: str) -> str:
    return re.sub("@\u200b*", "@\u200b", markdown.replace("<", "&lt;"))


def _review_line(
    code: str,
    approvers: list[str],
    others: list[str],
    maintainers: Mapping[str, list[str]],
    day: int | None,
    *,
    failed: bool,
    reported: bool,
) -> str:
    if failed:
        line = f"`{code}`  Review  waiting for the checks to pass"
    elif approvers:
        line = f"`{code}`  Review  verified by {', '.join(f'@{a}' for a in approvers)}"
    else:
        listed = maintainers.get(code.lower(), [])
        names = ", ".join(f"@{m}" for m in listed[:MAX_LISTED_MAINTAINERS]) if listed else "(none yet)"
        if len(listed) > MAX_LISTED_MAINTAINERS:
            names += ", …"
        line = f"`{code}`  Review  needs native review · maintainer: {names} · day {day or 0} of {WAIT_DAYS}"
    if not reported:
        line += " · no report"
    if others and not failed:
        line += f" · approved by {', '.join(f'@{o}' for o in others)} — not a listed maintainer, needs confirmation"
    return f"- {line}"


def decide(
    report: dict[str, Any],
    reviews: Iterable[Review],
    author: str,
    maintainers: Mapping[str, list[str]],
    current_labels: set[str],
    applied_at: datetime | None,
    now: datetime,
    report_markdown: str,
    head_sha: str,
    languages: Sequence[str] | None = None,
    *,
    beyond: bool = False,
) -> Decision:
    """Work out label changes and the comment; `languages` overrides the report's own language list."""
    codes = sorted(report["languages"] if languages is None else languages)
    if not codes:
        return Decision(set(), set(), "", False)
    reviews = list(reviews)
    failed = report["failed"]
    day = waiting_day(applied_at, now) if NEEDS_REVIEW in current_labels else None
    unreported = [code for code in codes if code not in report["languages"]]
    review_lines: list[str] = []
    approved = True
    for code in codes:
        approvers = qualifying_approvers(reviews, author, code, maintainers, head_sha)
        others = other_approvers(reviews, author, code, maintainers, head_sha)
        approved = approved and bool(approvers)
        review_lines.append(
            _review_line(code, approvers, others, maintainers, day, failed=failed, reported=code not in unreported)
        )
    if beyond:
        review_lines.append(f"- {BEYOND_NOTE}")

    add = {BASE}
    remove: set[str] = set()
    notice = False
    if failed:
        remove |= {NEEDS_REVIEW, UNVERIFIED, VERIFIED}
    elif beyond:
        add.add(NEEDS_REVIEW)
        remove |= {VERIFIED, UNVERIFIED}
    elif approved:
        add.add(VERIFIED)
        remove |= {NEEDS_REVIEW, UNVERIFIED}
    else:
        add.add(NEEDS_REVIEW)
        remove.add(VERIFIED)
        if day is not None and day >= WAIT_DAYS:
            add.add(UNVERIFIED)
            notice = UNVERIFIED not in current_labels

    state = {"languages": codes, "failed": failed, "head_sha": head_sha, "beyond": beyond, "no_report": unreported}
    head = f"{MARKER}\n{STATE_PREFIX}{json.dumps(state)} -->\n"
    tail = _REVIEW_HEADING + "\n".join(review_lines) + "\n"
    body = _sanitise_markdown(report_markdown)
    budget = max(COMMENT_LIMIT - len(head.encode()) - len(tail.encode()) - 100, 0)
    if len(body.encode()) > budget:
        body = body.encode()[:budget].decode("utf-8", errors="ignore") + "\n\n_(report truncated)_"
    return Decision(add, remove, head + body + tail, notice)


def classify_files(filenames: Iterable[str]) -> tuple[list[str], bool]:
    """Return the languages whose translation surfaces changed, and whether anything else changed."""
    languages: set[str] = set()
    beyond = False
    for name in filenames:
        if name == _ENGLISH_STRINGS:
            continue
        codes = [m.group(1) for pattern in _SURFACES if (m := pattern.fullmatch(name))]
        if codes and codes[0].lower() != "en" and _CODE.fullmatch(codes[0]):
            languages.add(codes[0])
        else:
            beyond = True
    return sorted(languages), beyond


def validate_artifact_pr(raw: str, pr_head_sha: str, run_head_sha: str) -> int:
    """Return the pull request number from the artifact, or raise ValueError when it cannot be trusted."""
    number = parse_pr_number(raw)
    if not _SHA.fullmatch(pr_head_sha) or pr_head_sha != run_head_sha:
        msg = "pull request head does not match the workflow run"
        raise ValueError(msg)
    return number


def parse_pr_number(raw: str) -> int:
    """Return a positive integer from untrusted text, or raise ValueError."""
    text = raw.strip()
    if not (text.isascii() and text.isdigit()) or int(text) <= 0:
        msg = "pr.txt is not a positive integer"
        raise ValueError(msg)
    return int(text)


def parse_maintainers(text: str) -> dict[str, list[str]]:
    """Parse the maintainers file; anything unexpected means no maintainers for that entry."""
    try:
        data = yaml.safe_load(text) if text.strip() else None
    except yaml.YAMLError:
        return {}
    languages = data.get("languages") if isinstance(data, dict) else None
    if not isinstance(languages, dict):
        return {}
    result: dict[str, list[str]] = {}
    for code, logins in languages.items():
        if isinstance(code, str) and isinstance(logins, list):
            result[code.lower()] = [str(x).lower() for x in logins if isinstance(x, str)]
    return {code: logins for code, logins in result.items() if logins}


def _gh(*args: str, stdin: str | None = None) -> Any:
    """Call `gh api` with an argument list and return the decoded JSON output; `stdin` is the request body."""
    command = ["gh", "api", *args] + (["--input", "-"] if stdin is not None else [])
    result = subprocess.run(command, input=stdin, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        msg = f"gh api {args[0]} failed: {result.stderr.strip()}"
        raise RuntimeError(msg)
    return json.loads(result.stdout) if result.stdout.strip() else None


def _paged(path: str) -> list[Any]:
    pages = _gh("--paginate", "--slurp", path) or []
    return [item for page in pages for item in (page if isinstance(page, list) else [page])]


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def _fetch_maintainers(repo: str, default_branch: str) -> dict[str, list[str]]:
    try:
        data = _gh(f"repos/{repo}/contents/{MAINTAINERS_PATH}?ref={quote(default_branch, safe='')}")
    except RuntimeError as err:
        if "404" in str(err) or "Not Found" in str(err):
            return {}
        raise
    if not isinstance(data, dict) or not isinstance(data.get("content"), str):
        return {}
    return parse_maintainers(base64.b64decode(data["content"]).decode("utf-8", errors="replace"))


def _fetch_reviews(repo: str, number: int) -> list[Review]:
    return [
        Review(item["user"]["login"], item["state"], _parse_time(item["submitted_at"]), item.get("commit_id") or "")
        for item in _paged(f"repos/{repo}/pulls/{number}/reviews")
        if item.get("user") and item.get("submitted_at")
    ]


def _applied_at(repo: str, number: int) -> datetime | None:
    times = [
        _parse_time(event["created_at"])
        for event in _paged(f"repos/{repo}/issues/{number}/events")
        if event.get("event") == "labeled" and (event.get("label") or {}).get("name") == NEEDS_REVIEW
    ]
    return max(times, default=None)


def _bot_comments(repo: str, number: int) -> list[dict[str, Any]]:
    return [
        item
        for item in _paged(f"repos/{repo}/issues/{number}/comments")
        if (item.get("user") or {}).get("login") == BOT_LOGIN and str(item.get("body", "")).startswith(MARKER)
    ]


def _state_from_comment(body: str) -> tuple[dict[str, Any], str] | None:
    match = _STATE_LINE.search(body)
    if not match:
        return None
    try:
        state = json.loads(match.group(1))
    except ValueError:
        return None
    if not isinstance(state, dict):
        return None
    for key in ("languages", "no_report"):
        codes = state.get(key, [])
        if not (isinstance(codes, list) and all(isinstance(c, str) and _CODE.fullmatch(c) for c in codes)):
            return None
    if not (isinstance(state.get("failed"), bool) and isinstance(state.get("head_sha"), str)):
        return None
    markdown = body[match.end() :].rsplit(_REVIEW_HEADING, 1)[0].strip("\n")
    return state, markdown


def _apply(repo: str, pr: dict[str, Any], decision: Decision, existing: list[dict[str, Any]]) -> None:
    number = pr["number"]
    current = {label["name"] for label in pr.get("labels", [])}
    for label in sorted(decision.add - current):
        _gh("-X", "POST", f"repos/{repo}/issues/{number}/labels", stdin=json.dumps({"labels": [label]}))
    for label in sorted(decision.remove & current):
        _gh("-X", "DELETE", f"repos/{repo}/issues/{number}/labels/{quote(label, safe='')}")
    if not decision.comment:
        return
    body = json.dumps({"body": decision.comment})
    if existing:
        _gh("-X", "PATCH", f"repos/{repo}/issues/comments/{existing[0]['id']}", stdin=body)
    else:
        _gh("-X", "POST", f"repos/{repo}/issues/{number}/comments", stdin=body)
    if decision.post_unverified_notice:
        notice = (
            f"No listed native speaker has approved these translations within {WAIT_DAYS} days, so they are labelled "
            "unverified. They can still be merged; a listed maintainer's approval will verify them."
        )
        _gh("-X", "POST", f"repos/{repo}/issues/{number}/comments", stdin=json.dumps({"body": notice}))


def _drop_stale_labels(repo: str, pr: dict[str, Any]) -> None:
    """Remove verified and unverified, which only ever describe the head they were computed for."""
    current = {label["name"] for label in pr.get("labels", [])}
    for label in sorted({VERIFIED, UNVERIFIED} & current):
        _gh("-X", "DELETE", f"repos/{repo}/issues/{pr['number']}/labels/{quote(label, safe='')}")


def _changed_files(repo: str, number: int) -> list[str]:
    names: list[str] = []
    for item in _paged(f"repos/{repo}/pulls/{number}/files"):
        names.append(str(item["filename"]))
        if item.get("previous_filename"):
            names.append(str(item["previous_filename"]))
    return names


def _triage(
    repo: str,
    pr: dict[str, Any],
    report: dict[str, Any],
    markdown: str,
    maintainers: Mapping[str, list[str]],
) -> None:
    number = pr["number"]
    languages, beyond = classify_files(_changed_files(repo, number))
    if len(languages) > MAX_LANGUAGES:
        print(f"#{number}: too many languages; no action taken", file=sys.stderr)
        _drop_stale_labels(repo, pr)
        return
    labels = {label["name"] for label in pr.get("labels", [])}
    decision = decide(
        report,
        _fetch_reviews(repo, number),
        pr["user"]["login"],
        maintainers,
        labels,
        _applied_at(repo, number) if NEEDS_REVIEW in labels else None,
        datetime.now(UTC),
        markdown,
        pr["head"]["sha"],
        languages,
        beyond=beyond,
    )
    if not decision.comment:
        _drop_stale_labels(repo, pr)
        return
    _apply(repo, pr, decision, _bot_comments(repo, number))


def _read_artifact(path: Path) -> str:
    with path.open("rb") as handle:
        return handle.read(_MAX_ARTIFACT_BYTES).decode("utf-8", errors="replace")


def _run(
    repo: str, artifact: Path, run_head_sha: str, run_conclusion: str, maintainers: Mapping[str, list[str]]
) -> int:
    raw = _read_artifact(artifact / "pr.txt")
    try:
        number = parse_pr_number(raw)
        pr = _gh(f"repos/{repo}/pulls/{number}")
        validate_artifact_pr(raw, pr["head"]["sha"], run_head_sha)
    except ValueError as err:
        print(f"artifact rejected: {err}", file=sys.stderr)
        return 1
    if pr.get("state") != "open":
        return 0
    try:
        report = validate_report(json.loads(_read_artifact(artifact / "report.json")))
    except ValueError:
        report = None
    if report is None:
        print("report.json has an unexpected shape; no action taken", file=sys.stderr)
        _drop_stale_labels(repo, pr)
        return 0
    report = {**report, "failed": report["failed"] or run_conclusion != "success"}
    _triage(repo, pr, report, _read_artifact(artifact / "report.md"), maintainers)
    return 0


def _daily(repo: str, maintainers: Mapping[str, list[str]]) -> int:
    status = 0
    for pr in _paged(f"repos/{repo}/pulls?state=open&per_page=100"):
        if BASE not in {label["name"] for label in pr.get("labels", [])}:
            continue
        try:
            comments = _bot_comments(repo, pr["number"])
            parsed = _state_from_comment(comments[0]["body"]) if comments else None
            if parsed is None or parsed[0]["head_sha"] != pr["head"]["sha"]:
                print(f"#{pr['number']}: no current report state; skipped", file=sys.stderr)
                _drop_stale_labels(repo, pr)
                continue
            state, markdown = parsed
            reported = set(state["languages"]) - set(state.get("no_report", []))
            report = {"failed": state["failed"], "languages": {code: {} for code in sorted(reported)}}
            _triage(repo, pr, report, markdown, maintainers)
        except Exception as err:  # noqa: BLE001
            print(f"#{pr.get('number')}: {type(err).__name__}: {err}", file=sys.stderr)
            status = 1
    return status


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run")
    run.add_argument("--artifact", type=Path, required=True)
    run.add_argument("--run-head-sha", required=True)
    run.add_argument("--run-conclusion", required=True)
    sub.add_parser("daily")
    args = parser.parse_args(argv)

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not _REPO.fullmatch(repo):
        print("GITHUB_REPOSITORY is not set to owner/name", file=sys.stderr)
        return 1
    default_branch = _gh(f"repos/{repo}")["default_branch"]
    maintainers = _fetch_maintainers(repo, default_branch)
    if args.mode == "run":
        return _run(repo, args.artifact, args.run_head_sha, args.run_conclusion, maintainers)
    return _daily(repo, maintainers)


if __name__ == "__main__":
    sys.exit(main())
