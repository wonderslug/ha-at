# Translations: contribution and validation — design

## Intent

The maintainer speaks only English and cannot judge whether a translation is correct. Contributors should have one
clear, documented path to add a language, and the maintainer should be able to decide whether to merge a pull request
in a language they cannot read. The project does that by shifting the trust onto two things the maintainer _can_ read:
an automated report that proves the translation is complete and behaves as claimed, and an approving review from a
second native speaker.

## Goals

- A contributor can add or update a language for every user-visible surface: the UI strings, the sidebar panel, and the
  voice and time language pack.
- Every translation pull request gets one report comment that states completeness, behaviour and review status per
  language, readable without speaking the language.
- A second native speaker's approval is the normal route to merge; after 30 days without one, the language can ship
  marked _unverified_ and be verified later.
- One contributor document covers the whole process.

## Non-goals

- Machine back-translation, external translation platforms (Lokalise, Weblate, Crowdin).
- Translating the language pack's Python logic for the contributor, or making voice packs writable without Python.
- Any new language in this work. This builds the path; languages arrive through it.

## Anti-goals

- A check that fails every English pull request because other languages lag behind. Lagging is reported, never fatal.
- Running a contributor's code with a write token. Pull requests come from forks.
- Merging automatically. Automation labels and reports; the maintainer merges.

## Decisions taken in conversation

- **Voice and time packs stay Python, written by developers.** Time grammar differs too much between languages to be
  data ("halb acht", compound number words, "moins le quart"). What makes a pack checkable is a required table of
  examples, not a data format.
- **The panel becomes translatable the way Home Assistant's KNX panel is.** Its strings move into the integration's
  translation files under the `config_panel` section; the panel loads them with `hass.loadBackendTranslation` and reads
  them with `hass.localize`. hassfest accepts `config_panel` with nested keys, and the installed Home Assistant
  (2026.10) serves any category through `frontend/get_translations`.
- **Review policy:** a second native speaker approves; if nobody does within **30 days**, the maintainer may merge with
  the language marked unverified. A later qualifying review flips it to verified. Updates to a language with a listed
  maintainer go to that maintainer, with the same 30-day fallback.
- **Whose approval qualifies:** a language's first reviewer is confirmed by the repository maintainer, who applies
  `translation: verified` by hand and adds that reviewer to the language's maintainer list in the same pull request.
  From then on, an approving review from a listed maintainer of that language (not the author) flips the label
  automatically. Any other approval is reported ("approved by X, not a listed maintainer") and changes nothing.
- **Pull request templates and labels** drive the process, with a path-based labeler so labelling never depends on the
  contributor choosing a template.
- **CI approach:** pytest checks plus a dedicated translation workflow that posts a report (option 2 of three).

## Approaches considered

1. **Checks folded into the existing test suite.** No new workflow; failures are buried among the other tests and
   there is no per-language summary. Rejected: the summary is what replaces reading the language.
2. **Same checks plus a dedicated workflow with a sticky report comment and the review automation. — chosen.** The
   checks still run in `script/test`; the workflow runs them on translation changes and turns the results into one
   comment per pull request.
3. **A standalone plain-Python checker for JSON, pytest only for packs.** Splits the checks across two tools for a
   speed gain the suite does not need.

## Design

### The three surfaces

| Surface             | File                                      | Who writes it     | Who reviews meaning              |
| ------------------- | ----------------------------------------- | ----------------- | -------------------------------- |
| UI strings + panel  | `translations/<lang>.json`                | Anyone, no code   | Native speaker                   |
| Voice and time pack | `lang/<lang>.py`                          | Developer         | Native speaker, via the examples |
| Voice examples      | `tests/translations/examples/<lang>.yaml` | The pack's author | Native speaker                   |

A language may ship strings without a voice pack; each surface is reported and verified separately.

The examples file is the native reviewer's main reading for a voice pack: plain sentences and their expected results,
no regex. The reviewer judges whether a person would say them; CI proves the pack does what they say.

### Phase 1 — panel strings into the translation files

- Every user-visible English string in `frontend/src` moves to `translations/en.json` under `config_panel`, grouped by
  component (`config_panel.upcoming.*`, `config_panel.add_job.*`, …). Date and time formatting already uses `Intl` with
  the user's locale and stays as is.
- The panel calls `hass.loadBackendTranslation("config_panel", "at")` on start and renders
  `hass.localize("component.at.config_panel.<key>", …)`. A missing key falls back to English, as Home Assistant does
  for every category.
- Frontend tests mock `localize` from `en.json`, so the existing assertions on English text keep working.

### Phase 2 — the checks (`tests/translations/`)

Check functions live in one module that both pytest and the report script import, so the two can never disagree.

**Strings, per `translations/<lang>.json` other than `en.json`:**

| Check                                                             | Severity                                           |
| ----------------------------------------------------------------- | -------------------------------------------------- |
| Valid JSON, only keys that exist in `en.json`                     | fail                                               |
| Same `{placeholders}` as the English string                       | fail                                               |
| hassfest value rules (no HTML, no leading/trailing space, no URL) | fail                                               |
| Keys present in English but missing here                          | report                                             |
| Value identical to English                                        | report (some words are the same in both languages) |

hassfest validates only `en.json`, so these checks are the only validation other languages get.

**Voice packs, per pack registered in `lang._PACKS`:**

| Check                                                                              | Severity |
| ---------------------------------------------------------------------------------- | -------- |
| An examples file exists for the pack                                               | fail     |
| Every example produces its expected result                                         | fail     |
| Each example sentence lands in its expected group, by the runtime's own precedence | fail     |
| Response, logbook, to-do and message templates keep English's placeholders         | fail     |
| A required example category has no examples                                        | report   |
| A sentence group English has is empty in this pack                                 | report   |

"Required categories" are what every pack must demonstrate: relative times, absolute clock times, day words, weekdays,
named times, spelled-out numbers, schedule, list, cancel, run, announce (area, floor, everyone). A category English adds
later shows up as "report" for older packs, so English work never breaks them.

Example file shape:

```yaml
language: de
now: "2026-11-17 22:22" # fixed reference time, in the test time zone
times:
  - category: relative
    text: "in zwanzig Minuten"
    expect: "2026-11-17 22:42"
  - category: clock
    text: "um halb acht"
    expect: "2026-11-18 07:30"
sentences:
  - text: "erinnere mich in 10 Minuten das Licht auszuschalten"
    group: schedule
    slots: { command: "das Licht auszuschalten" }
  - text: "welche Aufgaben sind geplant"
    group: list
```

Time examples run through the time parser; sentence examples run through the same matcher and group order the
runtime uses (`cancel`, `list`, `announce`, `schedule`, `run`; earlier wins a tie), with no Home Assistant instance.
English legitimately overlaps ("run X in 30 minutes" fits `run` and `schedule`), so the check is "the runtime picks the
expected group", not "only one group matches". English gets an examples file too,
converted from the existing test tables, so it serves as the template contributors copy.

### Phase 3 — the workflows

Two workflows, split by trust:

- **`translations.yml`** — on `pull_request` when `custom_components/at/translations/**`, `custom_components/at/lang/**`
  or `tests/translations/**` change. Read-only token. Runs the translation tests and `script/translations-report`,
  which writes the report as Markdown plus a small JSON (languages, surfaces, pass/fail), and uploads both as an
  artifact. Fails the job on any "fail" check.
- **`translations-triage.yml`** — on `workflow_run` of the first, and on a daily schedule. Write token, never checks
  out pull request code; reads only the artifact and the GitHub API. It:
  - posts or edits the single report comment;
  - applies `translation`, and `translation: needs native review` while no qualifying approval exists;
  - mentions the language's maintainers from `.github/translation-maintainers.yml`, read from the default branch so a
    pull request cannot add its own author and approve itself;
  - flips to `translation: verified` when a listed maintainer of that language other than the author approves; any other
    approval is named in the report as "not a listed maintainer — needs confirmation";
  - adds a comment and `translation: unverified` eligibility once 30 days have passed since `needs native review` was
    applied with the checks green.

Review comment shape:

```text
Translation report — de
  Strings + panel   162/164 keys   2 missing: config.step.user.data.x, …
  Placeholders      all kept
  Untranslated      3 identical to English (listed)
  Voice pack        58/58 examples pass · categories 12/13 (missing: named times)
  Review            needs native review · maintainer: (none yet) · day 4 of 30
```

### Phase 4 — labels, template, documentation

- **Labels** in `.github/labels.yml`, created by a small workflow on push to `main` (`gh label create --force`):
  `translation`, `translation: needs native review`, `translation: verified`, `translation: unverified`.
- **Pull request template** `.github/PULL_REQUEST_TEMPLATE/translation.md`: language and surfaces, whether the author is
  a native speaker, how it was tried (live or tests only, per `AI_POLICY.md`), and a request for a reviewer. The default
  template stays; the docs link to `…/compare?template=translation.md`.
- **`docs/user/TRANSLATING.md`**:
  - the three surfaces and what each needs;
  - step by step for strings only, and for a voice pack with its examples;
  - running the checks locally (`script/test tests/translations`, `script/translations-report`);
  - how to ask for, and how to give, a native review;
  - what verified and unverified mean;
  - the language table: language, surfaces, status, and a link to the maintainer list.
- **`.github/translation-maintainers.yml`**: language code → GitHub logins. The triage workflow's only source of who
  qualifies; the documentation links to it instead of copying it. Edited only by the repository maintainer when
  confirming a first reviewer.
- `CONTRIBUTING.md` links to it; the `ha-translations` skill points agents at it for anything beyond `en.json`.

## Constraints

- Template sync: `custom_components/` and `tests/` are sync-ignored; the new workflow, template and labels files are new
  paths the blueprint does not ship, so sync leaves them alone.
- Actions are pinned by commit SHA with the version in a comment, as in the existing workflows, and declare least
  permissions.
- The project rule that agents only edit `en.json` stays; this design is for human contributors.

## Left to the builder

- Exact `config_panel` key names and grouping.
- How the report script and pytest share the check module.
- The comment's exact wording and formatting beyond the shape above.
- How examples express expectations for list, cancel and announce sentences beyond `group` and `slots`.
