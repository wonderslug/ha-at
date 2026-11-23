# Translations Contribution and Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let contributors add a language for the UI strings, the panel and the voice pack, and let a maintainer who
cannot read it judge the pull request from an automated report plus a listed native speaker's approval.

**Architecture:** Check functions in `tests/translations/checks.py` are run both by pytest and by a report module that
emits Markdown and JSON. A read-only `translations.yml` workflow produces that report as an artifact; a privileged
`translations-triage.yml` turns it into a sticky comment and labels, using pure logic in
`script/.lib/translation_triage.py`. The panel moves its strings into `translations/en.json` under `config_panel` and
reads them through `hass.localize`.

**Tech Stack:** Python 3.14, pytest + pytest-homeassistant-custom-component, hassil, PyYAML; TypeScript + Lit + vitest
for the panel; GitHub Actions with `gh`.

**Spec:** [`docs/superpowers/specs/2026-11-22-translations-design.md`](../specs/2026-11-22-translations-design.md)

## Global Constraints

- Waiting period: **30 days**, counted from when `translation: needs native review` was applied with checks green.
- Labels, exactly: `translation`, `translation: needs native review`, `translation: verified`, `translation: unverified`.
- Qualifying approval: an `APPROVED` review, latest per reviewer, by a login listed for that language in
  `.github/translation-maintainers.yml` **as read from the default branch**, and not the pull request author.
- Missing keys and missing example categories are **reported, never failed**. Fail only on: unknown keys, changed
  placeholders, hassfest value rules, a registered pack without an examples file, an example with the wrong result, a
  pack template with different placeholders than English.
- The privileged workflow never checks out or executes pull request code.
- Actions pinned by commit SHA with `# vX.Y.Z`; `permissions: {}` at top level, least permissions per job.
- Agents edit only `en.json` (project rule); no other language file is created by this plan.
- Panel strings use plain `{name}` placeholders only — no ICU plural or select. Phrase count-dependent text so it does
  not need one (`"Jobs: {count}"`).
- Translation keys match `^(?!.+[_-]{2})(?![_-])[a-z0-9-_]+(?<![_-])$` (hassfest).
- Validation loop per AGENTS.md: `script/lint`, `script/type-check`, `script/hassfest`, `script/test` — never raw tools.
  Frontend: `npm --prefix frontend run typecheck`, `npm --prefix frontend test`, `npm --prefix frontend run build`.

## Review Focus

- **Fork pull request numbers:** `workflow_run.pull_requests` is empty for forks. The triage must take the number from
  the artifact, reject anything not a positive integer, and refuse when that PR's head SHA differs from
  `workflow_run.head_sha` (Task 7, `test_artifact_pr_mismatch_is_rejected`).
- **A pull request that edits the maintainer list:** the author adds themselves, then approves from a second account.
  Must not verify, because the list is read from `main` (Task 7, `test_maintainers_added_in_pr_do_not_count`).
- **English-only change:** adding a key to `en.json` must not label the pull request `translation` or fail any other
  language (Task 4, `test_en_only_paths_select_no_language`; Task 2, `test_missing_key_is_reported_not_failed`).
- **The user switches language while the panel is open:** the panel must reload `config_panel` for the new language
  (Task 5, `reloads translations when hass.language changes`).
- **Approval then change request by the same maintainer:** only the latest review per reviewer counts (Task 7,
  `test_latest_review_per_reviewer_wins`).

---

## File structure

| File                                                                          | Responsibility                                           |
| ----------------------------------------------------------------------------- | -------------------------------------------------------- |
| `custom_components/at/ha_internal/sentence_triggers.py`                       | `SentenceGroup.name`, public `match_sentence()`          |
| `custom_components/at/voice/triggers.py`                                      | public `sentence_groups()` — the group order             |
| `tests/translations/checks.py`                                                | every check, as pure functions returning `Finding`s      |
| `tests/translations/examples/en.yaml`                                         | English examples; the template contributors copy         |
| `tests/translations/test_strings.py`, `test_packs.py`                         | unit tests for checks + parametrized run over real files |
| `tests/translations/report.py`, `test_report.py`                              | Markdown + JSON report, changed-language detection       |
| `script/translations-report`                                                  | shell wrapper running the report in the venv             |
| `frontend/src/localize.ts`                                                    | `makeLocalize()`; panel loading of `config_panel`        |
| `script/.lib/translation_triage.py`                                           | approvals, labels, waiting period, comment, `gh` calls   |
| `script/tests/test_translation_triage.py`                                     | its tests                                                |
| `.github/workflows/translations.yml`, `translations-triage.yml`, `labels.yml` | the three workflows                                      |
| `.github/labels.yml`, `.github/translation-maintainers.yml`                   | label definitions; language → logins                     |
| `.github/PULL_REQUEST_TEMPLATE/translation.md`                                | translation pull request template                        |
| `docs/user/TRANSLATING.md`                                                    | contributor guide                                        |

---

### Task 1: Named sentence groups and a public matcher

**Files:**

- Modify: `custom_components/at/ha_internal/sentence_triggers.py` (`SentenceGroup`, `on_trigger` in
  `async_register_sentence_triggers`)
- Modify: `custom_components/at/voice/triggers.py:96-201` (`_language_sentences`)
- Test: `tests/voice/test_sentence_match.py`

**Interfaces:**

- Produces:
  - `SentenceGroup(name: str, sentences: list[str], callback: TriggerCallback)` — `name` is the first field.
  - `@dataclass(frozen=True) class SentenceMatch: group: SentenceGroup; wildcards: dict[str, str]; spans: dict[str, tuple[int, int]]`
  - `match_sentence(language: LanguageSentences, text: str, parser: Intents | None = None) -> SentenceMatch | None` —
    `recognize_best` over `_parser(language)` (or the given parser), wildcard values through `_value_text`.
  - `sentence_groups(pack: LanguagePack, *, defer_relative: bool) -> list[tuple[str, list[str]]]` in `voice/triggers.py`,
    returning exactly `cancel`, `list`, `announce`, `schedule`, `run` in that order; `schedule` is
    `schedule_absolute` plus `schedule_relative` unless `defer_relative`; `announce` is `trigger_sentences(pack)`.

- [ ] **Step 1: Write the failing tests** in `tests/voice/test_sentence_match.py`, building
      `LanguageSentences("en", [SentenceGroup(name, s, _noop) for name, s in sentence_groups(EN, defer_relative=False)], EN.sentence_lists, _noop)`:

```python
def test_group_order() -> None:
    assert [name for name, _ in sentence_groups(EN, defer_relative=False)] == ["cancel", "list", "announce", "schedule", "run"]

def test_defer_relative_drops_relative_schedule() -> None:
    groups = dict(sentence_groups(EN, defer_relative=True))
    assert not set(EN.sentences["schedule_relative"]) & set(groups["schedule"])

@pytest.mark.parametrize(("text", "group"), [
    ("in 10 minutes turn off the kitchen light", "schedule"),
    ("what's scheduled", "list"),
    ("cancel all jobs", "cancel"),
    ("cancel the 6am job", "cancel"),
    ("run the morning routine", "run"),
])
def test_match_sentence_picks_group(text: str, group: str) -> None:
    match = match_sentence(EN_SENTENCES, text)
    assert match is not None and match.group.name == group

def test_match_sentence_returns_wildcards() -> None:
    match = match_sentence(EN_SENTENCES, "in 10 minutes turn off the kitchen light")
    assert match.wildcards["command"] == "turn off the kitchen light"

def test_unmatched_sentence_returns_none() -> None:
    assert match_sentence(EN_SENTENCES, "what is the weather") is None
```

- [ ] **Step 2: Run to verify they fail** — `script/test tests/voice/test_sentence_match.py`; expected: ImportError on
      `match_sentence` / `sentence_groups`.
- [ ] **Step 3: Implement** the interfaces above. `on_trigger` calls `match_sentence(language, user_input.text, parser)`
      and dispatches to `match.group.callback`, so runtime and checks share one code path. `_language_sentences` zips
      `sentence_groups()` with a `{name: callback}` dict.
- [ ] **Step 4: Run** `script/test tests/voice` — all pass, including the unchanged `test_triggers.py`.
- [ ] **Step 5: Commit** — `refactor(voice): name sentence groups and share one matcher with the runtime`.

### Task 2: String checks

**Files:**

- Create: `tests/translations/__init__.py`, `tests/translations/checks.py`
- Test: `tests/translations/test_strings.py`

**Interfaces:**

- Produces (in `checks.py`):
  - `Severity = Literal["fail", "report"]`
  - `@dataclass(frozen=True) class Finding: severity: Severity; kind: str; key: str; detail: str = ""`
  - `TRANSLATIONS_DIR: Path`, `def translation_languages() -> list[str]` — codes of every `*.json` except `en`.
  - `@dataclass class StringsResult: language: str; keys_total: int; keys_present: int; findings: list[Finding]`
  - `def check_strings(english: Mapping[str, Any], other: Mapping[str, Any], language: str) -> StringsResult`
  - `kind` values: `unknown_key`, `placeholders`, `html`, `whitespace`, `url`, `missing_key`, `identical`.

- [ ] **Step 1: Write the failing tests** with small in-memory dicts:

```python
EN = {"config": {"step": {"user": {"title": "Set up {name}", "data": {"x": "Delay"}}}}}

def test_complete_translation_has_no_findings(): ...           # keys_present == keys_total == 2, findings == []
def test_unknown_key_fails(): ...                              # extra "config.step.user.bogus" -> fail/unknown_key
def test_changed_placeholder_fails(): ...                      # "Einrichten {nom}" -> fail/placeholders, key "config.step.user.title"
def test_dropped_placeholder_fails(): ...                      # "Einrichten" -> fail/placeholders
def test_html_fails(): ...                                     # "<b>Verzögerung</b>" -> fail/html
def test_leading_or_trailing_space_fails(): ...                # " Verzögerung" -> fail/whitespace
def test_url_fails(): ...                                      # "see https://x.y" -> fail/url
def test_missing_key_is_reported_not_failed(): ...             # omit data.x -> report/missing_key, keys_present == 1
def test_identical_to_english_is_reported(): ...               # "Delay" -> report/identical
def test_non_object_json_root_fails(): ...                     # check_strings(EN, [], "de") -> fail/unknown_key key ""
```

Plus the real-file run:

```python
@pytest.mark.parametrize("language", translation_languages())
def test_translation_file(language: str) -> None:
    result = check_strings(load(TRANSLATIONS_DIR / "en.json"), load(TRANSLATIONS_DIR / f"{language}.json"), language)
    assert [f for f in result.findings if f.severity == "fail"] == []
```

(Empty parametrization is fine today; it collects as skipped.)

- [ ] **Step 2: Run to verify they fail** — `script/test tests/translations/test_strings.py`.
- [ ] **Step 3: Implement** `check_strings`: flatten both to dotted keys; placeholders compared as sets via
      `re.findall(r"\{(\w+)\}", s)`; HTML is `re.search(r"<[a-zA-Z/]", s)`; URL is `re.search(r"https?://", s)`. Keys
      that exist in English with a non-string value in the translation count as `unknown_key`.
- [ ] **Step 4: Run** — pass.
- [ ] **Step 5: Commit** — `test(translations): check translated strings against English`.

### Task 3: Voice-pack checks and the English examples

**Files:**

- Modify: `tests/translations/checks.py`
- Create: `tests/translations/examples/en.yaml`
- Test: `tests/translations/test_packs.py`

**Interfaces:**

- Consumes: `match_sentence`, `SentenceGroup`, `LanguageSentences` (Task 1); `sentence_groups` (Task 1);
  `parse_time_text`, `resolve`, `TimeParseError` from `core/timeparse.py`; `lang._PACKS`, `get_language_pack`.
- Produces:
  - `EXAMPLES_DIR: Path`; `TIME_CATEGORIES = ("relative", "clock", "day", "weekday", "named", "spelled_number")`;
    `SENTENCE_GROUPS = ("schedule", "list", "cancel", "run", "announce")`.
  - `@dataclass class PackResult: language: str; examples_total: int; examples_passed: int; categories_missing: list[str]; findings: list[Finding]`
  - `def check_pack(pack: LanguagePack, examples: Mapping[str, Any] | None, english: LanguagePack) -> PackResult`
  - New `kind` values: `no_examples`, `time_example`, `sentence_example`, `template_placeholders`,
    `missing_category`, `empty_group`, `bad_examples`.
- Examples file schema (`language`, `now` as `"%Y-%m-%d %H:%M"`, optional `time_zone` default `America/Chicago`):
  - `times[]`: `category` (one of `TIME_CATEGORIES`), `text`, `expect` (`"%Y-%m-%d %H:%M"` local, or `null` meaning
    `TimeParseError`).
  - `sentences[]`: `text`, `group` (one of `SENTENCE_GROUPS`), optional `slots` (subset of the match's wildcards).

- [ ] **Step 1: Write `examples/en.yaml`** from the existing tables in `tests/core/test_timeparse.py` (`NOW` and `TZ`
      there are the values to use) and `tests/voice/test_triggers.py`, at least two examples per category and group,
      plus one `expect: null`.
- [ ] **Step 2: Write the failing tests**, using small hand-built example dicts against `EN`:

```python
def test_english_examples_all_pass():                        # check_pack(EN, load(en.yaml), EN): passed == total, no fail, categories_missing == []
def test_missing_examples_file_fails():                      # check_pack(EN, None, EN) -> fail/no_examples
def test_wrong_time_expectation_fails():                     # "in 20 minutes" expect "…22:43" -> fail/time_example, detail names got and expected
def test_expected_unparseable_that_parses_fails():           # "in 20 minutes" expect null -> fail/time_example
def test_sentence_in_wrong_group_fails():                    # run-sentence labelled "schedule" -> fail/sentence_example
def test_slot_mismatch_fails():                              # slots {command: "x"} -> fail/sentence_example
def test_missing_category_is_reported():                     # no weekday examples -> report/missing_category "weekday"
def test_template_placeholder_change_fails():                # dataclasses.replace(EN, responses={**EN.responses, k: "no fields"}) -> fail/template_placeholders
def test_empty_group_is_reported():                          # replace(EN, sentences={**EN.sentences, "run": []}) -> report/empty_group
def test_malformed_examples_fail():                          # {"times": [{"text": "x"}]} -> fail/bad_examples, not an exception

@pytest.mark.parametrize("code", list(_PACKS))
def test_registered_pack(code: str):                         # every registered pack: no "fail" findings
```

- [ ] **Step 3: Run to verify they fail** — `script/test tests/translations/test_packs.py`.
- [ ] **Step 4: Implement** `check_pack`. Template placeholders: for every `LanguagePack` field whose English value is a
      `str`, or a `Mapping` whose values are `str`, compare `string.Formatter().parse` field names key by key; callables
      and keys absent from the translation are skipped. Empty groups: a `pack.sentences` key English has non-empty and
      this pack has empty or missing.
- [ ] **Step 5: Run** — pass.
- [ ] **Step 6: Commit** — `test(translations): check voice packs against their examples`.

### Task 4: The report

**Files:**

- Create: `tests/translations/report.py`, `script/translations-report`
- Test: `tests/translations/test_report.py`

**Interfaces:**

- Consumes: `check_strings`, `check_pack`, `translation_languages`, `Finding` (Tasks 2–3).
- Produces:
  - `def languages_from_paths(paths: Iterable[str]) -> list[str]` — sorted codes from
    `custom_components/at/translations/<x>.json`, `custom_components/at/lang/<x>.py`,
    `tests/translations/examples/<x>.yaml`, excluding `en` and `lang/__init__.py`.
  - `def build_report(languages: Sequence[str]) -> dict[str, Any]` — JSON shape, consumed by Task 7:

```json
{
  "failed": false,
  "languages": {
    "de": {
      "strings": {
        "status": "pass|fail|absent",
        "keys_total": 164,
        "keys_present": 162,
        "findings": [{ "severity": "", "kind": "", "key": "", "detail": "" }]
      },
      "voice": {
        "status": "pass|fail|absent",
        "examples_total": 58,
        "examples_passed": 58,
        "categories_missing": [],
        "findings": []
      }
    }
  }
}
```

- `def render_markdown(report: dict[str, Any]) -> str` — one block per language in the spec's shape, without the
  Review line (Task 7 adds it). Lists at most 10 keys per finding kind, then "… and N more".
- `def main(argv: list[str] | None = None) -> int` — `--changed-files PATH` (newline-separated) or `--all`;
  `--json PATH`, `--markdown PATH`; returns 1 when `failed`.
- `script/translations-report` — header block per `blueprint.shell`, `activate_venv`, then
  `python -m tests.translations.report "$@"`.

- [ ] **Step 1: Write the failing tests:**

```python
def test_en_only_paths_select_no_language():   # ["custom_components/at/translations/en.json", "custom_components/at/lang/en.py"] -> []
def test_paths_select_languages():             # de.json + lang/fr.py + examples/fr.yaml + lang/__init__.py -> ["de", "fr"]
def test_absent_surface():                     # language with json only -> voice.status == "absent"
def test_failed_reflects_any_fail():           # monkeypatch check_strings to return a fail finding -> failed True, main returns 1
def test_markdown_lists_missing_keys():        # 12 missing keys -> 10 shown and "… and 2 more"
def test_main_writes_both_files(tmp_path):     # --all --json --markdown -> both exist, json parses
```

- [ ] **Step 2: Run to verify they fail** — `script/test tests/translations/test_report.py`.
- [ ] **Step 3: Implement** the interfaces; `build_report` loads `lang.get_language_pack(code)` only when
      `code in _PACKS` and the examples file if it exists.
- [ ] **Step 4: Run** `script/test tests/translations` and `script/translations-report --all --markdown /dev/stdout` —
      pass, prints a report with no languages.
- [ ] **Step 5: Commit** — `test(translations): render a per-language report`.

### Task 5: Panel localisation plumbing

**Files:**

- Create: `frontend/src/localize.ts`, `frontend/test/localize.test.ts`, `frontend/test/en-localize.ts`
- Modify: `frontend/src/types.ts` (`HomeAssistant`), `frontend/src/at-panel.ts`
- Modify: `custom_components/at/translations/en.json` — add `config_panel` with the `at-panel.ts` strings

**Interfaces:**

- Produces:
  - `HomeAssistant` gains `localize(key: string, values?: Record<string, string | number>): string` and
    `loadBackendTranslation(category: string, integration?: string): Promise<unknown>`.
  - `export type Localize = (key: string, values?: Record<string, string | number>) => string;`
  - `export function makeLocalize(hass: HomeAssistant): Localize` — prefixes `component.at.config_panel.`; returns the
    key itself when `hass.localize` returns `""`.
  - `AtPanel` calls `hass.loadBackendTranslation("config_panel", "at")` on start and again whenever `hass.language`
    changes, then `requestUpdate()`; components receive `localize` as a property `.localize=${...}`.
  - `frontend/test/en-localize.ts`: `export function enHass(partial: Partial<HomeAssistant>): HomeAssistant` whose
    `localize` reads `config_panel` from `custom_components/at/translations/en.json` and substitutes `{x}`.

- [ ] **Step 1: Write the failing tests** in `frontend/test/localize.test.ts`:
  - `makeLocalize prefixes the key` — stub `localize` records `"component.at.config_panel.upcoming.title"`.
  - `makeLocalize falls back to the key` — stub returns `""` → result `"upcoming.title"`.
  - `panel loads config_panel on start` — `loadBackendTranslation` called with `("config_panel", "at")`.
  - `reloads translations when hass.language changes` — set a new `hass` with `language: "de"` → called twice.
- [ ] **Step 2: Run** `npm --prefix frontend test` — fails.
- [ ] **Step 3: Implement**, move `at-panel.ts`'s own strings to `en.json` `config_panel.panel.*`, run `script/hassfest`.
- [ ] **Step 4: Run** `npm --prefix frontend run typecheck && npm --prefix frontend test && npm --prefix frontend run build`
      and `script/hassfest` — pass.
- [ ] **Step 5: Commit** (bundle included) — `feat(panel): load panel text from the translation files`.

### Task 6: Move every panel string

**Files:**

- Modify: `frontend/src/components/*.ts`, `frontend/src/source.ts`, `frontend/src/add-job.ts`, `frontend/src/format.ts`
  (only literal English, not `Intl` calls), and their tests in `frontend/test/`
- Modify: `custom_components/at/translations/en.json` (`config_panel.<component>.*`)

**Interfaces:**

- Consumes: `Localize`, `enHass` (Task 5). Pure helpers that produce text (for example in `source.ts`) take a
  `localize: Localize` parameter instead of reading `hass`.
- Out of scope: the sidebar title (`PANEL_TITLE`) and job summaries, which the backend writes in the job's language.

- [ ] **Step 1: Switch the tests** of one component at a time to `enHass(...)`; they must still assert the same English
      text, proving each key resolves.
- [ ] **Step 2: Replace** that component's literals with `localize("<component>.<key>", {...})` and add the keys to
      `en.json`.
- [ ] **Step 3: Repeat** until `rg -n '"[A-Z][a-z]+ [a-z]' frontend/src` shows no user-visible literals (review each
      hit; CSS and log strings stay).
- [ ] **Step 4: Run** the frontend trio, `script/hassfest`, `script/test tests/translations` — pass; `npm run build`
      leaves the committed bundle current.
- [ ] **Step 5: Commit** — `feat(panel): make every panel string translatable`.

### Task 7: Triage logic

**Files:**

- Create: `script/.lib/translation_triage.py`, `.github/translation-maintainers.yml` (`languages: {}`)
- Test: `script/tests/test_translation_triage.py`

**Interfaces:**

- Consumes: the report JSON (Task 4).
- Produces (stdlib + PyYAML only):
  - `WAIT_DAYS = 30`, `MARKER = "<!-- at-translation-report -->"`, the four label names as constants.
  - `@dataclass(frozen=True) class Review: login: str; state: str; submitted_at: datetime`
  - `def latest_reviews(reviews: Iterable[Review]) -> dict[str, Review]`
  - `def qualifying_approvers(reviews, author: str, language: str, maintainers: Mapping[str, list[str]]) -> list[str]`
  - `def other_approvers(reviews, author: str, language: str, maintainers) -> list[str]` — approved, not listed.
  - `def waiting_day(applied_at: datetime | None, now: datetime) -> int | None`
  - `@dataclass class Decision: add: set[str]; remove: set[str]; comment: str; post_unverified_notice: bool`
  - `def decide(report: dict, reviews, author: str, maintainers, current_labels: set[str], applied_at: datetime | None, now: datetime) -> Decision`
    - no languages in report → empty `Decision` (no comment).
    - always add `translation`; `verified` when every language has a qualifying approver, else
      `needs native review`; `unverified` added once `waiting_day >= WAIT_DAYS` and `report["failed"]` is false,
      with `post_unverified_notice` true only the first time.
    - `comment` = `MARKER` + Task 4 Markdown + per-language Review line:
      `Review  verified by @x` / `needs native review · maintainer: @a, @b | (none yet) · day N of 30` / plus
      `approved by @y — not a listed maintainer, needs confirmation`.
  - `def validate_artifact_pr(raw: str, pr_head_sha: str, run_head_sha: str) -> int` — raises `ValueError` unless a
    positive integer and SHAs equal.
  - `def main(argv) -> int` — modes `run --artifact DIR --run-head-sha SHA` and `daily`; reads maintainers with
    `gh api repos/{repo}/contents/.github/translation-maintainers.yml?ref={default}`; applies labels and upserts the
    comment by `MARKER` via `gh api`; finds `applied_at` from the issue's `labeled` timeline events.

- [ ] **Step 1: Write the failing tests:**

```python
def test_no_languages_means_no_action()
def test_unlisted_approval_does_not_verify()           # comment names "@y — not a listed maintainer"
def test_listed_maintainer_approval_verifies()          # add has VERIFIED, remove has NEEDS_REVIEW
def test_author_approval_never_counts()                 # author is a listed maintainer, approves own PR
def test_latest_review_per_reviewer_wins()               # APPROVED then CHANGES_REQUESTED -> not verified
def test_every_language_needs_a_qualifying_approver()    # de verified, fr not -> needs review
def test_maintainers_added_in_pr_do_not_count()          # decide() is given main's list; the PR's list is never read — assert main() fetches with ref=default branch (mock gh)
def test_day_29_not_unverified() / test_day_30_unverified_once()
def test_failed_checks_block_unverified()
def test_artifact_pr_mismatch_is_rejected()              # "12; rm -rf", "0", and SHA mismatch -> ValueError
def test_comment_starts_with_marker()
```

- [ ] **Step 2: Run** `script/test script/tests/test_translation_triage.py` — fails.
- [ ] **Step 3: Implement.** `gh` calls go through one `_gh(*args: str) -> Any` helper so tests mock a single function.
- [ ] **Step 4: Run** — pass; `script/type-check` clean.
- [ ] **Step 5: Commit** — `ci: decide translation labels and the report comment`.

### Task 8: Workflows and labels

**Files:**

- Create: `.github/workflows/translations.yml`, `.github/workflows/translations-triage.yml`,
  `.github/workflows/labels.yml`, `.github/labels.yml`

**Interfaces:**

- Consumes: `script/translations-report` (Task 4), `script/.lib/translation_triage.py main` (Task 7).
- `translations.yml`: `pull_request` on `main` with `paths:` `custom_components/at/translations/**`,
  `custom_components/at/lang/**`, `tests/translations/**`; skip drafts as `lint.yml` does; `contents: read`. Steps:
  checkout (`persist-credentials: false`, `fetch-depth: 0`), mise and bootstrap as in `lint.yml`, write
  `git diff --name-only origin/main...HEAD` to a file, `script/test tests/translations`,
  `script/translations-report --changed-files … --json report/report.json --markdown report/report.md` (run even when
  the tests fail, `if: always()`), write `${{ github.event.number }}` to `report/pr.txt`, upload `report/` as artifact
  `translation-report`.
- `translations-triage.yml`: `workflow_run` (workflows: `Translations`, types `completed`) and
  `schedule: cron: "17 6 * * *"`; `pull-requests: write`, `issues: write`, `contents: read`, `actions: read`. Checks
  out the **default branch** only, downloads the artifact with `gh run download`, runs
  `python3 script/.lib/translation_triage.py run|daily`.
- `labels.yml`: on push to `main` touching `.github/labels.yml`, and `workflow_dispatch`; `issues: write`;
  `gh label create "<name>" --color … --description … --force` per entry.
- `.github/labels.yml`: the four labels with a colour and a one-line description each.

- [ ] **Step 1: Write** the four files; pin every action to the SHA already used in `lint.yml` /
      `copilot-setup-steps.yml`.
- [ ] **Step 2: Run** `script/lint` — yamllint and actionlint (if configured) pass.
- [ ] **Step 3: Verify the trust split by reading:** `translations-triage.yml` has no `ref:` pointing at the pull
      request and runs no `script/` other than the stdlib `translation_triage.py`.
- [ ] **Step 4: Commit** — `ci: report and triage translation pull requests`.

### Task 9: Template and contributor guide

**Files:**

- Create: `.github/PULL_REQUEST_TEMPLATE/translation.md`, `docs/user/TRANSLATING.md`
- Modify: `CONTRIBUTING.md` (one link), `.agents/skills/ha-translations/SKILL.md` (one pointer: contributor languages
  follow `docs/user/TRANSLATING.md`; the agent rule on `en.json` is unchanged)

- [ ] **Step 1: Write the template:** language code, surfaces (checkboxes: strings and panel, voice pack), "I am a
      native speaker" yes/no, how it was tried (live on Home Assistant / tests only — per `AI_POLICY.md`), "Reviewer I
      have asked:" line.
- [ ] **Step 2: Write `TRANSLATING.md`** with sentence-case sections: what can be translated; translating the strings
      and panel (copy `en.json`, keep keys and `{placeholders}`, leave missing keys out rather than copying English);
      adding a voice pack (copy `lang/en.py`, register in `_PACKS`, copy `examples/en.yaml`, every category); checking
      your work (`script/test tests/translations`, `script/translations-report --all`); opening the pull request (link
      `https://github.com/wonderslug/ha-at/compare/main...?template=translation.md`); reviewing as a native speaker
      (read the examples file and strings, approve or request changes); verified and unverified, and the 30 days;
      languages (table: language, surfaces, status; link to `.github/translation-maintainers.yml`). Follows the UI text
      style in `blueprint.markdown`.
- [ ] **Step 3: Run** `script/lint` and `script/skills-check` — pass.
- [ ] **Step 4: Commit** — `docs: explain how to contribute and review a translation`.

### Final check

- [ ] `script/lint`, `script/type-check`, `script/hassfest`, `script/test`, and the frontend trio all pass; record
      results in the pull request description per `AI_POLICY.md` (the workflows themselves are only exercised once a
      real translation pull request is opened — say so).
