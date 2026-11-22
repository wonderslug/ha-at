"""Tests for the privileged translation triage logic."""

import base64
from datetime import UTC, datetime, timedelta
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import pytest

_PATH = Path(__file__).parents[1] / ".lib" / "translation_triage.py"
_SPEC = importlib.util.spec_from_file_location("translation_triage", _PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
tt = importlib.util.module_from_spec(_SPEC)
sys.modules["translation_triage"] = tt
_SPEC.loader.exec_module(tt)

NOW = datetime(2026, 12, 1, tzinfo=UTC)
HEAD = "a" * 40
OLD = "b" * 40
MAINT = {"de": ["Anna", "bob"], "fr": ["claire"]}
REPORT = {"failed": False, "languages": {"de": {"strings": {"status": "pass"}, "voice": {"status": "absent"}}}}


def review(login: str, state: str = "APPROVED", hours: int = 0, commit: str = HEAD) -> Any:
    """Review."""
    return tt.Review(login, state, NOW - timedelta(days=5) + timedelta(hours=hours), commit)


def decide(report: dict = REPORT, reviews: list | None = None, **kwargs: Any) -> Any:
    """Decide."""
    args: dict[str, Any] = {
        "report": report,
        "reviews": reviews or [],
        "author": "dev",
        "maintainers": MAINT,
        "current_labels": set(),
        "applied_at": None,
        "now": NOW,
        "report_markdown": "REPORT BODY",
        "head_sha": HEAD,
    }
    args.update(kwargs)
    return tt.decide(**args)


def two_languages() -> dict:
    """Two languages."""
    return {"failed": False, "languages": {"de": {}, "fr": {}}}


def test_no_languages_means_no_action() -> None:
    """No languages means no action."""
    d = decide({"failed": False, "languages": {}})
    assert d == tt.Decision(set(), set(), "", False)


def test_unlisted_approval_does_not_verify() -> None:
    """Unlisted approval does not verify."""
    d = decide(reviews=[review("y")])
    assert tt.VERIFIED not in d.add
    assert tt.NEEDS_REVIEW in d.add
    assert "@y — not a listed maintainer" in d.comment


def test_listed_maintainer_approval_verifies_case_insensitively() -> None:
    """Listed maintainer approval verifies case insensitively."""
    d = decide(reviews=[review("anna")])
    assert tt.VERIFIED in d.add
    assert {tt.NEEDS_REVIEW, tt.UNVERIFIED} <= d.remove
    assert "verified by @anna" in d.comment


def test_author_approval_never_counts() -> None:
    """Author approval never counts."""
    d = decide(reviews=[review("bob")], author="Bob")
    assert tt.VERIFIED not in d.add


def test_latest_review_per_reviewer_wins() -> None:
    """Latest review per reviewer wins."""
    d = decide(reviews=[review("bob", hours=1), review("BOB", "CHANGES_REQUESTED", hours=2)])
    assert tt.VERIFIED not in d.add


def test_commented_review_does_not_cancel_approval() -> None:
    """Commented review does not cancel approval."""
    assert tt.VERIFIED in decide(reviews=[review("bob", hours=1), review("bob", "COMMENTED", hours=2)]).add


def test_approval_on_older_commit_does_not_verify() -> None:
    """Approval on older commit does not verify."""
    d = decide(reviews=[review("bob", commit=OLD)])
    assert tt.VERIFIED not in d.add
    assert tt.NEEDS_REVIEW in d.add


def test_every_language_needs_a_qualifying_approver() -> None:
    """Every language needs a qualifying approver."""
    d = decide(two_languages(), [review("bob")])
    assert tt.VERIFIED not in d.add
    assert tt.NEEDS_REVIEW in d.add
    assert decide(two_languages(), [review("bob"), review("claire")]).add >= {tt.VERIFIED}


def test_other_approvers_lists_unlisted_only() -> None:
    """Other approvers lists unlisted only."""
    reviews = [review("bob"), review("y"), review("dev")]
    assert tt.other_approvers(reviews, "dev", "de", MAINT, HEAD) == ["y"]
    assert tt.qualifying_approvers(reviews, "dev", "de", MAINT, HEAD) == ["bob"]


def test_waiting_day_and_unverified_threshold() -> None:
    """Waiting day and unverified threshold."""
    assert tt.waiting_day(None, NOW) is None
    applied = NOW - timedelta(days=29, hours=5)
    assert tt.waiting_day(applied, NOW) == 29
    assert tt.UNVERIFIED not in decide(applied_at=applied, current_labels={tt.NEEDS_REVIEW}).add


def test_day_30_unverified_once() -> None:
    """Day 30 unverified once."""
    applied = NOW - timedelta(days=30)
    first = decide(applied_at=applied, current_labels={tt.NEEDS_REVIEW})
    assert tt.UNVERIFIED in first.add
    assert first.post_unverified_notice
    again = decide(applied_at=applied, current_labels={tt.NEEDS_REVIEW, tt.UNVERIFIED})
    assert not again.post_unverified_notice


def test_failed_checks_block_unverified() -> None:
    """Failed checks block unverified."""
    d = decide({**REPORT, "failed": True}, applied_at=NOW - timedelta(days=40), current_labels={tt.NEEDS_REVIEW})
    assert tt.UNVERIFIED not in d.add


def test_artifact_pr_validation() -> None:
    """Artifact pr validation."""
    assert tt.validate_artifact_pr(" 12\n", HEAD, HEAD) == 12
    for raw in ("12; rm -rf", "0", "", "-3", "１２"):
        with pytest.raises(ValueError):
            tt.validate_artifact_pr(raw, HEAD, HEAD)
    with pytest.raises(ValueError):
        tt.validate_artifact_pr("12", HEAD, OLD)
    with pytest.raises(ValueError):
        tt.validate_artifact_pr("12", "abc", "abc")


def test_comment_structure() -> None:
    """Comment structure."""
    d = decide()
    lines = d.comment.split("\n")
    assert lines[0] == tt.MARKER
    state = json.loads(lines[1].removeprefix("<!-- at-translation-state ").removesuffix(" -->"))
    assert state == {"languages": ["de"], "failed": False, "head_sha": HEAD}
    assert "REPORT BODY" in d.comment
    assert "### Review" in d.comment


def test_oversized_markdown_is_truncated() -> None:
    """Oversized markdown is truncated."""
    d = decide(report_markdown="x" * 200_000)
    assert len(d.comment) <= 65_536
    assert "truncated" in d.comment
    assert "### Review" in d.comment


def test_markdown_cannot_forge_marker_state_or_mentions() -> None:
    """Markdown cannot forge marker state or mentions."""
    d = decide(report_markdown=f"{tt.MARKER}\n<!-- at-translation-state {{}} -->\n@someone")
    assert d.comment.count(tt.MARKER) == 1
    assert d.comment.count("<!-- at-translation-state") == 1
    assert "@someone" not in d.comment


@pytest.mark.parametrize(
    "report",
    [
        [],
        {"failed": "no", "languages": {}},
        {"failed": False, "languages": []},
        {"failed": False, "languages": {"de": "x"}},
        {"failed": False, "languages": {"--> <!--": {}}},
    ],
)
def test_malformed_report_is_rejected(report: Any) -> None:
    """Malformed report is rejected."""
    assert tt.validate_report(report) is None


def test_parse_maintainers_is_tolerant() -> None:
    """Parse maintainers is tolerant."""
    assert tt.parse_maintainers("") == {}
    assert tt.parse_maintainers("languages: {}") == {}
    assert tt.parse_maintainers("- a") == {}
    assert tt.parse_maintainers("languages: {de: bob, fr: [Claire, 3]}") == {"fr": ["claire"]}
    assert tt.parse_maintainers(": [") == {}


class FakeGh:
    """Records gh calls and answers them from canned data."""

    def __init__(self, *, maint: str = "languages: {de: [bob]}", comments: list | None = None) -> None:
        """Create the fake with canned maintainers and comments."""
        self.calls: list[tuple[str, ...]] = []
        self.maint = maint
        self.comments = comments or []
        self.reviews = [
            {"user": {"login": "bob"}, "state": "APPROVED", "submitted_at": "2026-11-28T00:00:00Z", "commit_id": HEAD}
        ]
        self.pr = {
            "number": 12,
            "state": "open",
            "user": {"login": "dev"},
            "head": {"sha": HEAD},
            "labels": [{"name": tt.NEEDS_REVIEW}],
        }

    def __call__(self, *args: str) -> Any:
        """Record and answer one gh call."""
        self.calls.append(args)
        path = next(a for a in args if a.startswith("repos/"))
        if path == "repos/o/r":
            return {"default_branch": "main"}
        if "contents/.github/translation-maintainers.yml" in path:
            return {"content": base64.b64encode(self.maint.encode()).decode()}
        if path.endswith("/reviews"):
            return [self.reviews]
        if path.endswith("/events"):
            return [[{"event": "labeled", "label": {"name": tt.NEEDS_REVIEW}, "created_at": "2026-10-01T00:00:00Z"}]]
        if path.endswith("/comments") and "-X" not in args:
            return [self.comments]
        if path.startswith("repos/o/r/pulls?"):
            return [[self.pr]]
        if path == "repos/o/r/pulls/12":
            return self.pr
        return None

    def writes(self) -> list[tuple[str, ...]]:
        """Writes."""
        return [c for c in self.calls if "-X" in c]


def artifact(tmp_path: Path, *, report: Any = REPORT, pr: str = "12") -> Path:
    """Artifact."""
    (tmp_path / "report.json").write_text(json.dumps(report))
    (tmp_path / "report.md").write_text("MD")
    (tmp_path / "pr.txt").write_text(pr)
    return tmp_path


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env."""
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")


def test_run_reads_maintainers_from_default_branch(env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Run reads maintainers from default branch."""
    gh = FakeGh()
    monkeypatch.setattr(tt, "_gh", gh)
    assert tt.main(["run", "--artifact", str(artifact(tmp_path)), "--run-head-sha", HEAD]) == 0
    fetches = [c for c in gh.calls if any("translation-maintainers.yml" in a for a in c)]
    assert len(fetches) == 1
    assert "ref=main" in " ".join(fetches[0])
    assert any(tt.VERIFIED in " ".join(c) for c in gh.writes())


def test_run_creates_comment_when_none_exists(env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Run creates comment when none exists."""
    gh = FakeGh()
    monkeypatch.setattr(tt, "_gh", gh)
    tt.main(["run", "--artifact", str(artifact(tmp_path)), "--run-head-sha", HEAD])
    assert any("repos/o/r/issues/12/comments" in c and "POST" in c for c in gh.writes())


def test_run_rejects_head_mismatch_without_writing(env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Run rejects head mismatch without writing."""
    gh = FakeGh()
    monkeypatch.setattr(tt, "_gh", gh)
    assert tt.main(["run", "--artifact", str(artifact(tmp_path)), "--run-head-sha", OLD]) == 1
    assert gh.writes() == []


def test_run_malformed_report_takes_no_action(env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Run malformed report takes no action."""
    gh = FakeGh()
    monkeypatch.setattr(tt, "_gh", gh)
    assert tt.main(["run", "--artifact", str(artifact(tmp_path, report={"languages": 3})), "--run-head-sha", HEAD]) == 0
    assert gh.writes() == []


def bot_comment(body: str, login: str = "github-actions[bot]") -> dict:
    """Bot comment."""
    return {"id": 99, "user": {"login": login}, "body": body}


def test_daily_ignores_marker_comment_by_other_user(env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Daily ignores marker comment by other user."""
    fake = decide().comment
    gh = FakeGh(comments=[bot_comment(fake, login="mallory")])
    gh.pr["labels"] = [{"name": tt.BASE}]
    monkeypatch.setattr(tt, "_gh", gh)
    assert tt.main(["daily"]) == 0
    assert gh.writes() == []


def test_daily_updates_bot_comment_and_labels(env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Daily updates bot comment and labels."""
    gh = FakeGh(comments=[bot_comment(decide().comment)])
    gh.pr["labels"] = [{"name": tt.BASE}, {"name": tt.NEEDS_REVIEW}]
    monkeypatch.setattr(tt, "_gh", gh)
    assert tt.main(["daily"]) == 0
    patches = [c for c in gh.writes() if "PATCH" in c]
    assert len(patches) == 1
    assert "repos/o/r/issues/comments/99" in patches[0]
    assert any(tt.VERIFIED in " ".join(c) for c in gh.writes())


def test_daily_skips_when_head_moved_since_report(env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Daily skips when head moved since report."""
    gh = FakeGh(comments=[bot_comment(decide(head_sha=OLD).comment)])
    monkeypatch.setattr(tt, "_gh", gh)
    assert tt.main(["daily"]) == 0
    assert gh.writes() == []
