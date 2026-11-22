#!/usr/bin/env python3
"""Decide translation labels and the sticky report comment for a pull request.

Runs in a privileged workflow on the default branch's code only. Everything read from the report artifact or from the
pull request is untrusted: it is validated, size-capped and never passed through a shell. Standard library and PyYAML
only.

Usage:
    translation_triage.py run --artifact DIR --run-head-sha SHA
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
COMMENT_LIMIT = 65_536
MAINTAINERS_PATH = ".github/translation-maintainers.yml"

_SHA = re.compile(r"[0-9a-f]{40}")
_CODE = re.compile(r"[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*")
_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
_STATE_LINE = re.compile(r"^<!-- at-translation-state (\{.*\}) -->$", re.MULTILINE)
_REVIEW_HEADING = "\n### Review\n"
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
    if not isinstance(languages, dict):
        return None
    for code, entry in languages.items():
        if not isinstance(code, str) or not _CODE.fullmatch(code) or not isinstance(entry, dict):
            return None
    return report


def _sanitise_markdown(markdown: str) -> str:
    cleaned = markdown.replace(MARKER, "").replace(STATE_PREFIX, "")
    return cleaned.replace("@", "@\u200b")


def _review_line(
    code: str,
    approvers: list[str],
    others: list[str],
    maintainers: Mapping[str, list[str]],
    day: int | None,
) -> str:
    if approvers:
        line = f"`{code}`  Review  verified by {', '.join(f'@{a}' for a in approvers)}"
    else:
        listed = maintainers.get(code.lower(), [])
        names = ", ".join(f"@{m}" for m in listed) if listed else "(none yet)"
        line = f"`{code}`  Review  needs native review · maintainer: {names} · day {day or 0} of {WAIT_DAYS}"
    if others:
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
) -> Decision:
    """Work out label changes and the comment for a validated report."""
    codes = sorted(report["languages"])
    if not codes:
        return Decision(set(), set(), "", False)
    reviews = list(reviews)
    day = waiting_day(applied_at, now)
    review_lines: list[str] = []
    verified = True
    for code in codes:
        approvers = qualifying_approvers(reviews, author, code, maintainers, head_sha)
        others = other_approvers(reviews, author, code, maintainers, head_sha)
        verified = verified and bool(approvers)
        review_lines.append(_review_line(code, approvers, others, maintainers, day))

    add = {BASE}
    remove: set[str] = set()
    notice = False
    if verified:
        add.add(VERIFIED)
        remove |= {NEEDS_REVIEW, UNVERIFIED}
    else:
        add.add(NEEDS_REVIEW)
        remove.add(VERIFIED)
        if day is not None and day >= WAIT_DAYS and not report["failed"]:
            add.add(UNVERIFIED)
            notice = UNVERIFIED not in current_labels

    state = {"languages": codes, "failed": report["failed"], "head_sha": head_sha}
    head = f"{MARKER}\n{STATE_PREFIX}{json.dumps(state)} -->\n"
    tail = _REVIEW_HEADING + "\n".join(review_lines) + "\n"
    body = _sanitise_markdown(report_markdown)
    budget = COMMENT_LIMIT - len(head) - len(tail) - 100
    if len(body) > budget:
        body = body[:budget] + "\n\n_(report truncated)_"
    return Decision(add, remove, head + body + tail, notice)


def validate_artifact_pr(raw: str, pr_head_sha: str, run_head_sha: str) -> int:
    """Return the pull request number from the artifact, or raise ValueError when it cannot be trusted."""
    text = raw.strip()
    if not (text.isascii() and text.isdigit()) or int(text) <= 0:
        msg = "pr.txt is not a positive integer"
        raise ValueError(msg)
    if not _SHA.fullmatch(pr_head_sha) or pr_head_sha != run_head_sha:
        msg = "pull request head does not match the workflow run"
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


def _gh(*args: str) -> Any:
    """Call `gh api` with an argument list and return the decoded JSON output."""
    result = subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=False)
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
    codes = state.get("languages") if isinstance(state, dict) else None
    if not (
        isinstance(codes, list)
        and all(isinstance(c, str) and _CODE.fullmatch(c) for c in codes)
        and isinstance(state.get("failed"), bool)
        and isinstance(state.get("head_sha"), str)
    ):
        return None
    markdown = body[match.end() :].split(_REVIEW_HEADING, maxsplit=1)[0].strip("\n")
    return state, markdown


def _apply(repo: str, pr: dict[str, Any], decision: Decision, existing: list[dict[str, Any]]) -> None:
    number = pr["number"]
    current = {label["name"] for label in pr.get("labels", [])}
    for label in sorted(decision.add - current):
        _gh("-X", "POST", f"repos/{repo}/issues/{number}/labels", "-f", f"labels[]={label}")
    for label in sorted(decision.remove & current):
        _gh("-X", "DELETE", f"repos/{repo}/issues/{number}/labels/{quote(label, safe='')}")
    if not decision.comment:
        return
    if existing:
        _gh("-X", "PATCH", f"repos/{repo}/issues/comments/{existing[0]['id']}", "-f", f"body={decision.comment}")
    else:
        _gh("-X", "POST", f"repos/{repo}/issues/{number}/comments", "-f", f"body={decision.comment}")
    if decision.post_unverified_notice:
        notice = (
            f"No listed native speaker has approved these translations within {WAIT_DAYS} days, so they are labelled "
            "unverified. They can still be merged; a listed maintainer's approval will verify them."
        )
        _gh("-X", "POST", f"repos/{repo}/issues/{number}/comments", "-f", f"body={notice}")


def _triage(
    repo: str,
    pr: dict[str, Any],
    report: dict[str, Any],
    markdown: str,
    maintainers: Mapping[str, list[str]],
) -> None:
    number = pr["number"]
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
    )
    _apply(repo, pr, decision, _bot_comments(repo, number))


def _read_artifact(path: Path) -> str:
    with path.open("rb") as handle:
        return handle.read(_MAX_ARTIFACT_BYTES).decode("utf-8", errors="replace")


def _run(repo: str, artifact: Path, run_head_sha: str, maintainers: Mapping[str, list[str]]) -> int:
    raw = _read_artifact(artifact / "pr.txt")
    text = raw.strip()
    if not (text.isascii() and text.isdigit()) or int(text) <= 0:
        print("pr.txt is not a positive integer", file=sys.stderr)
        return 1
    pr = _gh(f"repos/{repo}/pulls/{int(text)}")
    try:
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
        return 0
    _triage(repo, pr, report, _read_artifact(artifact / "report.md"), maintainers)
    return 0


def _daily(repo: str, maintainers: Mapping[str, list[str]]) -> int:
    for pr in _paged(f"repos/{repo}/pulls?state=open&per_page=100"):
        if BASE not in {label["name"] for label in pr.get("labels", [])}:
            continue
        comments = _bot_comments(repo, pr["number"])
        parsed = _state_from_comment(comments[0]["body"]) if comments else None
        if parsed is None or parsed[0]["head_sha"] != pr["head"]["sha"]:
            print(f"#{pr['number']}: no current report state; skipped", file=sys.stderr)
            continue
        state, markdown = parsed
        report = {"failed": state["failed"], "languages": {code: {} for code in state["languages"]}}
        _triage(repo, pr, report, markdown, maintainers)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run")
    run.add_argument("--artifact", type=Path, required=True)
    run.add_argument("--run-head-sha", required=True)
    sub.add_parser("daily")
    args = parser.parse_args(argv)

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not _REPO.fullmatch(repo):
        print("GITHUB_REPOSITORY is not set to owner/name", file=sys.stderr)
        return 1
    default_branch = _gh(f"repos/{repo}")["default_branch"]
    maintainers = _fetch_maintainers(repo, default_branch)
    if args.mode == "run":
        return _run(repo, args.artifact, args.run_head_sha, maintainers)
    return _daily(repo, maintainers)


if __name__ == "__main__":
    sys.exit(main())
