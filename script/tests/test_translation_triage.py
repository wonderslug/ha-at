"""Tests for the privileged translation triage logic."""

import base64
from datetime import UTC, datetime, timedelta
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import quote

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
    assert "@\u200by — not a listed maintainer" in d.comment


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
    assert state == {"languages": ["de"], "failed": False, "head_sha": HEAD, "beyond": False, "no_report": []}
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
        self.stdins: list[str] = []
        self.maint = maint
        self.comments = comments or []
        self.fail: set[int] = set()
        self.perms: dict[str, dict] = {}
        self.perm_errors: set[str] = set()
        self.files = [{"filename": "custom_components/at/translations/de.json"}]
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
        self.extra_prs: list[dict] = []

    def __call__(self, *args: str, stdin: str | None = None) -> Any:
        """Record and answer one gh call."""
        self.calls.append(args if stdin is None else (*args, stdin))
        if stdin is not None:
            self.stdins.append(stdin)
        path = next(a for a in args if a.startswith("repos/"))
        number = re.search(r"/(?:pulls|issues)/(\d+)/", path)
        if number and int(number.group(1)) in self.fail and "-X" not in args:
            msg = "boom"
            raise RuntimeError(msg)
        if path == "repos/o/r":
            return {"default_branch": "main"}
        if "/collaborators/" in path:
            login = path.split("/")[-2]
            if login in self.perm_errors:
                msg = "no access"
                raise RuntimeError(msg)
            return self.perms.get(login, {"permission": "read"})
        if "contents/.github/translation-maintainers.yml" in path:
            return {"content": base64.b64encode(self.maint.encode()).decode()}
        if path.endswith("/reviews"):
            return [self.reviews]
        if path.endswith("/files"):
            return [self.files]
        if path.endswith("/events"):
            return [[{"event": "labeled", "label": {"name": tt.NEEDS_REVIEW}, "created_at": "2026-10-01T00:00:00Z"}]]
        if path.endswith("/comments") and "-X" not in args:
            return [self.comments]
        if path.startswith("repos/o/r/pulls?"):
            return [[self.pr, *self.extra_prs]]
        if re.fullmatch(r"repos/o/r/pulls/\d+", path):
            return self.pr
        return None

    def writes(self) -> list[tuple[str, ...]]:
        """Return the mutating calls."""
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
    assert (
        tt.main(["run", "--artifact", str(artifact(tmp_path)), "--run-head-sha", HEAD, "--run-conclusion", "success"])
        == 0
    )
    fetches = [c for c in gh.calls if any("translation-maintainers.yml" in a for a in c)]
    assert len(fetches) == 1
    assert "ref=main" in " ".join(fetches[0])
    assert any(tt.VERIFIED in " ".join(c) for c in gh.writes())


def test_run_creates_comment_when_none_exists(env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Run creates comment when none exists."""
    gh = FakeGh()
    monkeypatch.setattr(tt, "_gh", gh)
    tt.main(["run", "--artifact", str(artifact(tmp_path)), "--run-head-sha", HEAD, "--run-conclusion", "success"])
    assert any("repos/o/r/issues/12/comments" in c and "POST" in c for c in gh.writes())


def test_run_rejects_head_mismatch_without_writing(env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Run rejects head mismatch without writing."""
    gh = FakeGh()
    monkeypatch.setattr(tt, "_gh", gh)
    assert (
        tt.main(["run", "--artifact", str(artifact(tmp_path)), "--run-head-sha", OLD, "--run-conclusion", "success"])
        == 0
    )
    assert gh.writes() == []


@pytest.mark.parametrize("name", ["report.json", "report.md"])
def test_missing_artifact_file_drops_stale_labels_without_raising(
    env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str
) -> None:
    """An unreadable artifact file never raises and never leaves a stale verified label."""
    gh = FakeGh()
    gh.pr["labels"] = list(STALE)
    artifact(tmp_path)
    (tmp_path / name).unlink()
    monkeypatch.setattr(tt, "_gh", gh)
    argv = ["run", "--artifact", str(tmp_path), "--run-head-sha", HEAD, "--run-conclusion", "success"]
    assert tt.main(argv) == 0
    assert sorted(deleted_labels(gh)) == sorted(quote(x, safe="") for x in (tt.VERIFIED, tt.UNVERIFIED))


def test_missing_pr_file_is_rejected_without_raising(
    env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Without a pull request number there is nothing to act on."""
    gh = FakeGh()
    artifact(tmp_path)
    (tmp_path / "pr.txt").unlink()
    monkeypatch.setattr(tt, "_gh", gh)
    argv = ["run", "--artifact", str(tmp_path), "--run-head-sha", HEAD, "--run-conclusion", "success"]
    assert tt.main(argv) == 1
    assert gh.writes() == []


def test_run_malformed_report_takes_no_action(env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Run malformed report takes no action."""
    gh = FakeGh()
    monkeypatch.setattr(tt, "_gh", gh)
    assert (
        tt.main(
            [
                "run",
                "--artifact",
                str(artifact(tmp_path, report={"languages": 3})),
                "--run-head-sha",
                HEAD,
                "--run-conclusion",
                "success",
            ]
        )
        == 0
    )
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


def run(gh: FakeGh, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, conclusion: str = "success", **kw: Any) -> int:
    """Run the privileged mode against the fake."""
    monkeypatch.setattr(tt, "_gh", gh)
    argv = ["run", "--artifact", str(artifact(tmp_path, **kw)), "--run-head-sha", HEAD, "--run-conclusion", conclusion]
    return tt.main(argv)


def posted_comment(gh: FakeGh) -> str:
    """Return the body of the first comment write."""
    return json.loads(next(s for s in gh.stdins if '"body"' in s))["body"]


def test_bodies_go_through_stdin_not_argv(env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Bodies are JSON on stdin."""
    gh = FakeGh()
    run(gh, monkeypatch, tmp_path)
    assert not any("body=" in a or "labels[]=" in a for c in gh.calls for a in c)
    assert tt.MARKER in posted_comment(gh)


def test_gh_helper_sends_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    """The real helper passes --input - and the data on stdin."""
    seen: dict[str, Any] = {}

    def fake_run(argv: list[str], **kwargs: Any) -> Any:
        seen.update(argv=argv, **kwargs)
        return type("R", (), {"returncode": 0, "stdout": "{}", "stderr": ""})()

    monkeypatch.setattr(tt.subprocess, "run", fake_run)
    tt._gh("-X", "POST", "repos/o/r/issues/1/comments", stdin='{"body": "x"}')  # noqa: SLF001
    assert seen["argv"][-2:] == ["--input", "-"]
    assert seen["input"] == '{"body": "x"}'


def test_sanitiser_is_idempotent() -> None:
    """Sanitising twice changes nothing more."""
    once = tt._sanitise_markdown("@a <b> @@c")  # noqa: SLF001
    assert tt._sanitise_markdown(once) == once  # noqa: SLF001


def test_comment_is_capped_in_bytes() -> None:
    """Multibyte and mention-heavy text stays well under the limit in bytes."""
    for text in ("é" * 100_000, "@" * 40_000):
        assert len(decide(report_markdown=text).comment.encode()) < 62_000


def test_huge_maintainer_list_cannot_break_the_budget() -> None:
    """The tail is bounded, so the body budget never goes negative."""
    d = decide(maintainers={"de": [f"user{i}" for i in range(20000)]}, report_markdown="x" * 1000)
    assert len(d.comment.encode()) < 65_536


def test_nested_payload_cannot_rebuild_marker() -> None:
    """Escaping defeats nested comment payloads."""
    d = decide(report_markdown="<!-- at-translation-" + tt.MARKER + "report -->")
    assert d.comment.count(tt.MARKER) == 1
    assert d.comment.count(tt.STATE_PREFIX) == 1
    assert d.comment.count("<!--") == 2


def test_unterminated_comment_cannot_hide_review() -> None:
    """An unterminated HTML comment is escaped."""
    d = decide(report_markdown="<!-- hidden")
    assert d.comment.count("<!--") == 2
    assert "### Review" in d.comment


def test_failed_then_green_restarts_the_clock() -> None:
    """Needs-review is removed while failed, and the wait restarts when green."""
    old = NOW - timedelta(days=40)
    failed = decide({**REPORT, "failed": True}, applied_at=old, current_labels={tt.BASE, tt.NEEDS_REVIEW})
    assert tt.NEEDS_REVIEW in failed.remove
    assert tt.NEEDS_REVIEW not in failed.add
    green = decide(applied_at=old, current_labels={tt.BASE})
    assert tt.UNVERIFIED not in green.add
    assert tt.NEEDS_REVIEW in green.add
    assert "day 0 of 30" in green.comment


def test_failed_run_is_never_verified() -> None:
    """Approval does not verify a failing run."""
    d = decide({**REPORT, "failed": True}, reviews=[review("bob")])
    assert tt.VERIFIED not in d.add


def test_classify_files() -> None:
    """Translation surfaces yield languages; anything else is beyond."""
    langs, beyond = tt.classify_files(
        [
            "custom_components/at/translations/de.json",
            "custom_components/at/lang/de.py",
            "tests/translations/examples/fr.yaml",
            "custom_components/at/translations/en.json",
        ]
    )
    assert (langs, beyond) == (["de", "fr"], False)
    for other in (
        "custom_components/at/lang/__init__.py",
        "custom_components/at/lang/en.py",
        "custom_components/at/__init__.py",
        "custom_components/at/translations/de.json.bak",
        "tests/translations/examples/en.yaml",
    ):
        assert tt.classify_files([other])[1] is True
    assert tt.classify_files([{"x": 1}][0:0]) == ([], False)


def test_languages_come_from_changed_files_not_the_report(
    env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A language without a report entry still needs approval; invented ones are ignored."""
    gh = FakeGh()
    gh.files = [
        {"filename": "custom_components/at/translations/de.json"},
        {"filename": "tests/translations/examples/fr.yaml"},
    ]
    report = {"failed": False, "languages": {"de": {}, "xx": {}}}
    run(gh, monkeypatch, tmp_path, report=report)
    body = posted_comment(gh)
    state = json.loads(body.split("\n")[1].removeprefix(tt.STATE_PREFIX).removesuffix(" -->"))
    assert state["languages"] == ["de", "fr"]
    assert state["no_report"] == ["fr"]
    assert "no report" in body
    assert not any(tt.VERIFIED in " ".join(c) for c in gh.writes())


def test_run_conclusion_failure_counts_as_failed(env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A non-success run conclusion fails the report even if report.json says otherwise."""
    gh = FakeGh()
    run(gh, monkeypatch, tmp_path, conclusion="cancelled")
    body = posted_comment(gh)
    assert '"failed": true' in body
    assert not any(tt.VERIFIED in " ".join(c) for c in gh.writes() if "labels" in " ".join(c))


def test_changes_beyond_translations_block_automatic_verification() -> None:
    """Extra code changes never get verified or unverified automatically."""
    d = decide(
        reviews=[review("bob")],
        beyond=True,
        applied_at=NOW - timedelta(days=40),
        current_labels={tt.NEEDS_REVIEW},
    )
    assert not d.add & {tt.VERIFIED, tt.UNVERIFIED}
    assert "This pull request also changes code beyond translations — confirm by hand." in d.comment
    assert '"beyond": true' in d.comment


def test_daily_honours_beyond_from_files(env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Daily re-fetches the files and still refuses to verify."""
    gh = FakeGh(comments=[bot_comment(decide().comment)])
    gh.pr["labels"] = [{"name": tt.BASE}, {"name": tt.NEEDS_REVIEW}]
    gh.files.append({"filename": "custom_components/at/__init__.py"})
    monkeypatch.setattr(tt, "_gh", gh)
    assert tt.main(["daily"]) == 0
    assert not any(tt.VERIFIED in " ".join(c) for c in gh.writes() if "labels" in " ".join(c))


def test_daily_continues_after_one_pr_fails(env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """One broken PR does not stop the others, but the exit code reports it."""
    gh = FakeGh(comments=[bot_comment(decide().comment)])
    gh.pr["labels"] = [{"name": tt.BASE}]
    gh.extra_prs = [{**gh.pr, "number": 13}]
    gh.fail = {12}
    monkeypatch.setattr(tt, "_gh", gh)
    assert tt.main(["daily"]) == 1
    assert len([c for c in gh.writes() if "PATCH" in c]) == 1


def test_parse_pr_number() -> None:
    """The shared parser accepts only positive ASCII integers."""
    assert tt.parse_pr_number("7\n") == 7
    for raw in ("", "0", "7;", "-1", "٣"):
        with pytest.raises(ValueError):
            tt.parse_pr_number(raw)


def test_language_count_is_capped() -> None:
    """More than 100 languages is rejected."""
    assert tt.validate_report(
        {"failed": False, "languages": {f"a{chr(97 + i % 26)}{chr(97 + i // 26)}": {} for i in range(100)}}
    )
    assert (
        tt.validate_report(
            {"failed": False, "languages": {f"a{chr(97 + i % 26)}{chr(97 + i // 26)}": {} for i in range(101)}}
        )
        is None
    )


def deleted_labels(gh: FakeGh) -> list[str]:
    """Return the label DELETE calls made."""
    return [c[-1].rsplit("/", 1)[-1] for c in gh.writes() if "DELETE" in c]


STALE = {"name": tt.BASE}, {"name": tt.VERIFIED}, {"name": tt.UNVERIFIED}


def test_beyond_removes_stale_verified() -> None:
    """A code change on a new head drops verified and unverified."""
    d = decide(beyond=True, current_labels={tt.BASE, tt.VERIFIED, tt.UNVERIFIED})
    assert {tt.VERIFIED, tt.UNVERIFIED} <= d.remove


def test_malformed_report_still_removes_stale_verified(
    env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The only write on a no-action path is dropping stale verified labels."""
    gh = FakeGh()
    gh.pr["labels"] = list(STALE)
    run(gh, monkeypatch, tmp_path, report={"languages": 3})
    assert len(gh.writes()) == 2
    assert sorted(deleted_labels(gh)) == sorted(quote(x, safe="") for x in (tt.VERIFIED, tt.UNVERIFIED))


def test_no_languages_still_removes_stale_verified(env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A head with no translation files cannot stay verified."""
    gh = FakeGh()
    gh.files = [{"filename": "README.md"}]
    gh.pr["labels"] = list(STALE)
    run(gh, monkeypatch, tmp_path)
    assert len(deleted_labels(gh)) == 2
    assert not [c for c in gh.writes() if "POST" in c]


def test_too_many_languages_still_removes_stale_verified(
    env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Too many languages is a no-action path that still drops verified."""
    gh = FakeGh()
    gh.files = [
        {"filename": f"custom_components/at/translations/a{chr(97 + i % 26)}{chr(97 + i // 26)}.json"}
        for i in range(101)
    ]
    gh.pr["labels"] = list(STALE)
    run(gh, monkeypatch, tmp_path)
    assert len(deleted_labels(gh)) == 2


def test_daily_with_moved_head_removes_stale_verified(env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """A stored report for an older head cannot keep verified."""
    gh = FakeGh(comments=[bot_comment(decide(head_sha=OLD).comment)])
    gh.pr["labels"] = list(STALE)
    monkeypatch.setattr(tt, "_gh", gh)
    assert tt.main(["daily"]) == 0
    assert len(deleted_labels(gh)) == 2
    assert not [c for c in gh.writes() if "POST" in c or "PATCH" in c]


def test_privileged_plus_other_approver_verifies() -> None:
    """A repository maintainer and one other approver verify every language."""
    d = decide(two_languages(), [review("rob"), review("sam")], privileged={"rob"})
    assert tt.VERIFIED in d.add
    assert "confirmed by @\u200brob (repository maintainer) with @\u200bsam" in d.comment


def test_privileged_approval_must_come_after_the_other() -> None:
    """The repository maintainer confirms a native speaker's approval, not the other way round."""
    after = decide(reviews=[review("sam", hours=0), review("rob", hours=1)], privileged={"rob"})
    before = decide(reviews=[review("rob", hours=0), review("sam", hours=1)], privileged={"rob"})
    assert tt.VERIFIED in after.add
    assert tt.VERIFIED not in before.add
    assert "approve again" in before.comment


def test_privileged_alone_does_not_verify() -> None:
    """A repository maintainer alone is not enough."""
    d = decide(reviews=[review("rob")], privileged={"rob"})
    assert tt.VERIFIED not in d.add
    assert (
        "repository maintainer approved — a native speaker's approval is still needed, then approve again" in d.comment
    )


def test_privileged_approval_on_older_commit_does_not_count() -> None:
    """Stale approvals never count, privileged or not."""
    d = decide(reviews=[review("rob", commit=OLD), review("sam")], privileged={"rob"})
    assert tt.VERIFIED not in d.add


def test_author_with_write_access_is_not_counted() -> None:
    """The author's own approval is ignored even with admin rights."""
    d = decide(reviews=[review("dev"), review("sam")], privileged={"dev"})
    assert tt.VERIFIED not in d.add


def test_beyond_blocks_privileged_verification() -> None:
    """Code changes beyond translations still block automatic verification."""
    d = decide(reviews=[review("rob"), review("sam")], privileged={"rob"}, beyond=True)
    assert tt.VERIFIED not in d.add


def two_reviewers(gh: FakeGh, *logins: str) -> None:
    """Make the fake return approvals on the current head by the given logins."""
    gh.reviews = [
        {"user": {"login": login}, "state": "APPROVED", "submitted_at": "2026-11-28T00:00:00Z", "commit_id": HEAD}
        for login in logins
    ]


def label_posts(gh: FakeGh) -> str:
    """Return the label POST payloads joined."""
    return " ".join(c[-1] for c in gh.writes() if "POST" in c and c[-2].endswith("/labels"))


def test_triage_builds_privileged_from_permission_api(
    env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Write access found through the API plus a second approver verifies."""
    gh = FakeGh()
    two_reviewers(gh, "rob", "sam")
    gh.perms = {"rob": {"permission": "write"}}
    run(gh, monkeypatch, tmp_path)
    assert tt.VERIFIED in label_posts(gh)


def test_role_name_is_accepted(env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The role name may carry the privilege."""
    gh = FakeGh()
    two_reviewers(gh, "rob", "sam")
    gh.perms = {"rob": {"permission": "read", "role_name": "maintain"}}
    run(gh, monkeypatch, tmp_path)
    assert tt.VERIFIED in label_posts(gh)


def test_permission_api_error_fails_closed(env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """An API error means not privileged."""
    gh = FakeGh()
    two_reviewers(gh, "rob", "sam")
    gh.perms = {"rob": {"permission": "admin"}}
    gh.perm_errors = {"rob"}
    run(gh, monkeypatch, tmp_path)
    assert tt.VERIFIED not in label_posts(gh)


def test_invalid_login_is_never_put_in_a_url(env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Only logins matching GitHub's pattern reach the permission endpoint."""
    gh = FakeGh()
    two_reviewers(gh, "../../x", "ok-user")
    run(gh, monkeypatch, tmp_path)
    called = [a for c in gh.calls for a in c if "/collaborators/" in a]
    assert called == ["repos/o/r/collaborators/ok-user/permission"]


def test_permission_checked_only_for_current_head_approvers(
    env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Stale approvers and the author cost no API call."""
    gh = FakeGh()
    two_reviewers(gh, "dev", "sam")
    gh.reviews.append({**gh.reviews[0], "user": {"login": "old"}, "commit_id": OLD})
    run(gh, monkeypatch, tmp_path)
    called = [a for c in gh.calls for a in c if "/collaborators/" in a]
    assert called == ["repos/o/r/collaborators/sam/permission"]


def review_line(d: Any, code: str = "de") -> str:
    """The comment's Review line for one language."""
    (line,) = [line for line in d.comment.splitlines() if line.startswith(f"- `{code}`")]
    return line


@pytest.mark.parametrize(
    ("reviews", "privileged", "expected"),
    [
        pytest.param(["bob"], set(), "- `de`  Review  verified by @bob", id="listed-maintainer"),
        pytest.param(
            ["rob", "sam"],
            {"rob"},
            "- `de`  Review  confirmed by @\u200brob (repository maintainer) with @\u200bsam",
            id="repository-maintainer-with-approver",
        ),
        pytest.param(
            ["rob"],
            {"rob"},
            "- `de`  Review  needs native review · maintainer: @Anna, @bob · day 0 of 30"
            " · repository maintainer approved — a native speaker's approval is still needed, then approve again"
            " · approved by @\u200brob — not a listed maintainer, needs confirmation",
            id="repository-maintainer-alone",
        ),
        pytest.param(
            ["y"],
            set(),
            "- `de`  Review  needs native review · maintainer: @Anna, @bob · day 0 of 30"
            " · approved by @\u200by — not a listed maintainer, needs confirmation",
            id="unlisted-approver",
        ),
        pytest.param(
            [], set(), "- `de`  Review  needs native review · maintainer: @Anna, @bob · day 0 of 30", id="none"
        ),
    ],
)
def test_review_line_in_each_state(reviews: list[str], privileged: set[str], expected: str) -> None:
    """Each Review line reads exactly as intended and mentions only listed maintainers."""
    d = decide(reviews=[review(login) for login in reviews], privileged=privileged)
    assert review_line(d) == expected


def test_unlisted_approver_beside_listed_maintainer_is_not_mentioned() -> None:
    """A non-maintainer approver is never mentioned, even on a verified line."""
    d = decide(reviews=[review("bob"), review("y")])
    assert review_line(d) == (
        "- `de`  Review  verified by @bob · approved by @\u200by — not a listed maintainer, needs confirmation"
    )
