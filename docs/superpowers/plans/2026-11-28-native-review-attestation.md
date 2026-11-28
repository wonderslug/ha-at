# Native Speaker Attestation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A translation approval verifies a language only when its review text attests native-speaker review of that
language, and labels update within minutes of a review.

**Architecture:** `script/.lib/translation_triage.py` reads each review's body, and `decide()` applies the attestation
rules per language. A new no-permission `Translation review` workflow fires on review events, and `Translation
triage` chains off it into the existing daily pass. `docs/user/TRANSLATING.md` puts the reviewer steps near the top.

**Tech Stack:** Python 3.14 standard library + PyYAML (the triage script's existing limits), pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-28-native-review-attestation-design.md`

## Global Constraints

- The triage script stays standard library + PyYAML only, and treats review text as untrusted data: fixed pattern
  match, capped length, never passed to a shell.
- The attestation line is exactly `Native speaker review: <code>`, on its own line, case-insensitive, surrounding
  spaces ignored; `_` and `-` in the code are equivalent.
- Agents cannot edit `.github/workflows/`; Task 3 is applied by the maintainer.
- Validation through the project scripts only: `script/lint`, `script/type-check`, `script/test`,
  `script/yaml-check`, `script/markdown`.
- Work on one branch, `ci/native-review-attestation`, from `origin/main`; one PR, squash-merged, title
  `ci(translations): require a native speaker attestation on translation approvals`.

## Review Focus

- A review whose API `body` is `null` or missing must count as having no attestation, not crash. (Task 1 test.)
- A quoted or indented line (`> Native speaker review: uk`, or the line inside a fenced block copied from the
  report) must not count; only a line that is the attestation itself counts. (Task 1 test.)
- A reviewer who attests only one language of a two-language PR verifies only that language. (Task 2 test.)
- A review body edited after submission to add the line counts on the next run, because bodies are read fresh and the
  review keeps its `APPROVED` state. (Task 2 test via `FakeGh`.)
- A `Translation review` run for a first-time contributor's fork PR may need workflow approval; the daily run is the
  fallback. Check on the first real review after merge. (Manual, Task 3.)

---

### Task 1: Read the attestation from reviews

**Files:**

- Modify: `script/.lib/translation_triage.py` (`Review` at line 60, `_fetch_reviews` at line 353, new constants near
  line 57)
- Test: `script/tests/test_translation_triage.py`

**Interfaces:**

- Produces: `Review.body: str = ""` (last field, defaulted so existing constructors keep working);
  `attests(body: str, language: str) -> bool`; `_MAX_REVIEW_BODY = 10_000`.

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.parametrize(
    ("body", "language", "expected"),
    [
        ("Native speaker review: uk", "uk", True),
        ("Looks good.\n  native SPEAKER review:   UK  \nThanks", "uk", True),
        ("Native speaker review: pt_BR", "pt-br", True),
        ("Native speaker review: de", "uk", False),
        ("> Native speaker review: uk", "uk", False),
        ("I did a Native speaker review: uk", "uk", False),
        ("", "uk", False),
    ],
)
def test_attests(body: str, language: str, expected: bool) -> None:
    """The attestation is a line of its own naming the language."""
    assert tt.attests(body, language) is expected


def test_attestation_past_the_cap_is_ignored() -> None:
    """Only the first _MAX_REVIEW_BODY characters are read."""
    assert not tt.attests("x" * tt._MAX_REVIEW_BODY + "\nNative speaker review: uk", "uk")


def test_fetch_reviews_reads_body_and_tolerates_null(env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """A null body reads as empty."""
    gh = FakeGh()
    gh.reviews = [
        {"user": {"login": "a"}, "state": "APPROVED", "submitted_at": "2026-11-28T00:00:00Z", "commit_id": HEAD,
         "body": "Native speaker review: de"},
        {"user": {"login": "b"}, "state": "APPROVED", "submitted_at": "2026-11-28T00:00:00Z", "commit_id": HEAD,
         "body": None},
    ]
    monkeypatch.setattr(tt, "_gh", gh)
    reviews = tt._fetch_reviews("o/r", 12)
    assert [r.body for r in reviews] == ["Native speaker review: de", ""]
```

- [ ] **Step 2: Run to verify they fail**

Run: `script/test script/tests/test_translation_triage.py -k "attest or fetch_reviews" -q`
Expected: FAIL, `attests` not defined.

- [ ] **Step 3: Implement**

`attests` truncates to `_MAX_REVIEW_BODY`, matches `re.compile(r"^[ \t]*native speaker review:[ \t]*(\S+)[ \t]*$", re.IGNORECASE | re.MULTILINE)`, and compares each match with the language after `.lower().replace("_", "-")` on both sides. `_fetch_reviews` passes `item.get("body") or ""` as `body`.

- [ ] **Step 4: Run to verify they pass**

Run: `script/test script/tests/test_translation_triage.py -q`
Expected: all pass (existing tests untouched so far).

- [ ] **Step 5: Commit**

```bash
git add script/.lib/translation_triage.py script/tests/test_translation_triage.py
git commit -m "ci(translations): read native speaker attestations from review text"
```

### Task 2: Count only attested approvals

**Files:**

- Modify: `script/.lib/translation_triage.py` (`qualifying_approvers`, `other_approvers`, `_review_line`, `decide`)
- Test: `script/tests/test_translation_triage.py`

**Interfaces:**

- Consumes: `Review.body`, `attests(body, language)` from Task 1.
- Produces: `qualifying_approvers` returns listed approvers whose latest review attests `language`;
  `other_approvers` returns unlisted approvers whose latest review attests `language`;
  `unattested_approvers(reviews, author, language, privileged, head_sha) -> list[str]`: current-head, non-author
  approvers who are not in `privileged` and whose latest review does not attest `language`.
  `decide()` keeps its signature. `PASTE_HINT` constant (exact copy below).

Rules, per language (spec table): listed + attested verifies; unlisted + attested needs a privileged approval at or
after it on the same head; a privileged approval needs no attestation; nothing else counts. The confirmation pair
moves inside the per-language loop: `(p, o)` with `p` privileged, `o != p`, `o` attests this language, both on head,
`latest[p].submitted_at >= latest[o].submitted_at`.

`_review_line` gains `unattested: list[str]` and appends, when not failed and non-empty:
``· approval by @​x has no `Native speaker review: <code>` line, not counted`` (zero-width space after `@`, as the
other lines do).

When the decision is not verified and not failed, the comment tail ends with `PASTE_HINT` formatted with every code
that has no counted approval, one attestation line each:

```text
To verify, a native speaker of the language selects **Review changes** > **Approve** on the latest commit and puts this line in the review text:

    Native speaker review: uk
```

- [ ] **Step 1: Update the test helpers and existing tests**

`ATTEST_DE = "Native speaker review: de"`; `review(...)` gains `body: str = ATTEST_DE` and passes it to `tt.Review`.
In `test_every_language_needs_a_qualifying_approver`, give `claire` `body="Native speaker review: fr"`. In
`test_privileged_plus_other_approver_verifies`, give `sam` `body="Native speaker review: de\nNative speaker review: fr"`.
`FakeGh` default reviews and `two_reviewers` add `"body": ATTEST_DE`.

- [ ] **Step 2: Write the failing tests**

```python
def test_listed_approval_without_attestation_does_not_verify() -> None:
    d = decide(reviews=[review("anna", body="LGTM")])
    assert tt.VERIFIED not in d.add
    assert "approval by @​anna has no `Native speaker review: de` line, not counted" in d.comment


def test_unlisted_attested_approval_needs_confirmation() -> None:
    d = decide(reviews=[review("sam")])
    assert tt.VERIFIED not in d.add
    assert "@​sam — not a listed maintainer, needs confirmation" in d.comment


def test_unlisted_unattested_approval_cannot_be_confirmed() -> None:
    d = decide(reviews=[review("sam", body="", hours=0), review("rob", body="", hours=1)], privileged={"rob"})
    assert tt.VERIFIED not in d.add


def test_confirmation_needs_no_attestation_from_the_maintainer() -> None:
    d = decide(reviews=[review("sam", hours=0), review("rob", body="", hours=1)], privileged={"rob"})
    assert tt.VERIFIED in d.add


def test_attestation_in_a_comment_review_does_not_count() -> None:
    assert tt.VERIFIED not in decide(reviews=[review("anna", "COMMENTED")]).add


def test_attestation_on_an_older_commit_does_not_count() -> None:
    assert tt.VERIFIED not in decide(reviews=[review("anna", commit=OLD)]).add


def test_author_attestation_never_counts() -> None:
    assert tt.VERIFIED not in decide(reviews=[review("bob")], author="bob").add


def test_attesting_one_language_verifies_only_that_one() -> None:
    d = decide(two_languages(), [review("anna"), review("claire", body="Native speaker review: de")])
    assert tt.VERIFIED not in d.add
    assert "Native speaker review: fr" in d.comment
    assert "    Native speaker review: de" not in d.comment


def test_paste_hint_shown_until_verified() -> None:
    assert "    Native speaker review: de" in decide().comment
    assert "Native speaker review:" not in decide(reviews=[review("anna")]).comment.split("### Review")[1]


def test_paste_hint_hidden_when_checks_failed() -> None:
    assert "    Native speaker review:" not in decide({"failed": True, "languages": {"de": {}}}).comment


def test_daily_counts_an_attestation_added_by_editing_the_review(env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Bodies are read fresh, so an edited approval counts on the next run."""
    # Build on test_daily_updates_bot_comment_and_labels: FakeGh's review for bob first has body "LGTM" (assert no
    # VERIFIED label post), then ATTEST_DE (assert a VERIFIED label post), same state and submitted_at.
```

- [ ] **Step 3: Run to verify they fail**

Run: `script/test script/tests/test_translation_triage.py -q`
Expected: the new tests FAIL; the updated existing tests pass or fail only on the new rules.

- [ ] **Step 4: Implement the rules above**

- [ ] **Step 5: Run to verify all pass**

Run: `script/test script/tests/test_translation_triage.py -q`, then `script/lint` and `script/type-check`.
Expected: all pass, both scripts exit 0.

- [ ] **Step 6: Commit**

```bash
git add script/.lib/translation_triage.py script/tests/test_translation_triage.py
git commit -m "ci(translations): count only approvals that attest native speaker review"
```

### Task 3: Run triage when a review is submitted (maintainer applies)

**Files:**

- Create: `.github/workflows/translation-review.yml`
- Modify: `.github/workflows/translations-triage.yml` (`on.workflow_run.workflows`, `daily` job `if`)

**Interfaces:**

- Consumes: the existing `daily` pass (`translation_triage.py daily`), unchanged.

- [ ] **Step 1: Hand the maintainer the exact changes**

`translation-review.yml`:

```yaml
name: Translation review

# Review events on fork pull requests only get a read-only token, so this workflow only signals; Translation triage
# chains off it with the write token.
on:
  pull_request_review:
    types: [submitted, edited, dismissed]

permissions: {}

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  signal:
    name: "Signal the triage"
    if: contains(github.event.pull_request.labels.*.name, 'translation')
    runs-on: ubuntu-26.04
    timeout-minutes: 2
    steps:
      - name: Record the review
        env:
          NUMBER: ${{ github.event.pull_request.number }}
        run: echo "Review event on #${NUMBER}"
```

`translations-triage.yml`: `workflows: [Translations, Translation review]`, and the `daily` job's `if` becomes
`github.event_name == 'schedule' || github.event_name == 'workflow_dispatch' || (github.event_name == 'workflow_run' && github.event.workflow_run.event == 'pull_request_review')`.
The `run` job's `if` already requires `workflow_run.event == 'pull_request'`, so it skips review-triggered runs.

- [ ] **Step 2: Validate once applied**

Run: `script/yaml-check`
Expected: `✓ YAML check completed`, zizmor reports no findings.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/translation-review.yml .github/workflows/translations-triage.yml
git commit -m "ci(translations): run triage when a translation review is submitted"
```

### Task 4: Document the reviewer steps

**Files:**

- Modify: `docs/user/TRANSLATING.md` (move "Reviewing as a native speaker" from line 143 to right after the intro,
  before "What can be translated"; adjust "Verified and unverified")
- Modify: `.github/PULL_REQUEST_TEMPLATE/translation.md`

- [ ] **Step 1: Rewrite the section**

Numbered steps: read the strings and panel; read `tests/translations/examples/<code>.yaml` if there is a voice pack;
select **Files changed** > **Review changes** > **Approve**; put the attestation line, in a `text` code block with
`uk` as the example, in the review text, with a sentence that the line must stand on its own and name the PR's
language, one line per language. Then what makes it count: the latest commit, not the author, your latest review,
an edited review counts, a new push needs a fresh approval, labels update within minutes. "Verified and unverified":
a listed reviewer's attested approval verifies; an unlisted reviewer's attested approval needs a maintainer's approval
after it. Keep UI labels bold and the page's existing style.

- [ ] **Step 2: Point reviewers at it from the template**

Add, above `## Language`, a visible line (reviewers read the rendered description, where HTML comments are hidden):

```markdown
> **Reviewing as a native speaker?** Approve and put the line `Native speaker review: <code>` in your review. Steps: [Reviewing as a native speaker](https://github.com/wonderslug/ha-at/blob/main/docs/user/TRANSLATING.md#reviewing-as-a-native-speaker).
```

- [ ] **Step 3: Validate**

Run: `script/markdown`
Expected: `0 issues`, `✓ Markdown formatting completed`.

- [ ] **Step 4: Commit**

```bash
git add docs/user/TRANSLATING.md .github/PULL_REQUEST_TEMPLATE/translation.md
git commit -m "docs(translations): put the native speaker reviewer steps first"
```

### Task 5: Ship

- [ ] **Step 1:** `script/lint`, `script/type-check`, `script/test` all exit 0 on the branch.
- [ ] **Step 2:** Push through the push gate (config change stashed), open the PR with the title from Global
      Constraints, wait for checks, squash-merge on the maintainer's go-ahead.
- [ ] **Step 3:** After merge, check the first real review on #64 or #65 produces a `Translation review` run and a
      `Translation triage` run that updates the report (Review Focus, last line).
