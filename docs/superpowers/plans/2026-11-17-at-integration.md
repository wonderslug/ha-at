# `at` Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `at`, a Home Assistant custom integration that runs one action, script or
automation once at a set time. It is driven by voice (Assist, both the built-in agent and
LLM agents), a sidebar panel, a to-do entity, sensors, and actions. Jobs are persistent and
keep a history.

**Architecture:**

- A pure-Python core (time parser, job model, store, manager/scheduler, executor) sits
  behind a `JobManager` that every surface talks to: voice, services, WebSocket and panel,
  entities.
- All dependence on HA internals goes through `ha_internal/`: recognize-only, programmatic
  sentence triggers, and running a stored intent. Phase 1 proves each one before anything
  is built on it.
- Language-specific text (time words, sentence templates, responses, summaries) lives in
  `lang/en.py` behind a `LanguagePack`.

**Tech Stack:**

- Backend: Python 3.14, Home Assistant 2026.10+, and the jpawlowski ha-integration-blueprint
  (uv, Ruff, Pyright, pytest-homeassistant-custom-component, prek, Release Please).
- Panel: TypeScript, Lit 3, Vite (library mode), Vitest.

**Spec:** `docs/superpowers/specs/2026-11-17-at-design.md`. Read it before any task. Section
numbers below (§) refer to it.

## Global Constraints

**Platform and naming**

- HA 2026.10+ and Python 3.14 (blueprint defaults). Domain `at`.
- `manifest.json` `name` is the placeholder `"at (placeholder)"`. The author sets the real
  name later. Sidebar title and device name come from the same constant, `DISPLAY_NAME`.
- `single_config_entry: true`, `integration_type: "service"`, `iot_class: "calculated"`.
- Don't copy code from scheduler-component, delayed_action, or any other existing project.

**Voice and safety**

- Never write into the user's `config/` directory. No `custom_sentences` files.
- An LLM never decides the time. All time parsing goes through `core/timeparse.py`.
- Voice may only reach entities exposed to Assist, both when a job is scheduled and when it
  fires (`assistant="conversation"`).
- English only ships. No English words in `core/`. All language text lives in `lang/en.py`.

**Storage and options**

- Store: key `at.jobs`, `version 1`, `minor_version 1`, with a migration hook in place.
- Option defaults:
  - grace window 5 min
  - history 7 days or 100 entries, whichever limit hits first
  - panel admin-only: off
  - "Let HA handle relative-time commands": off

**Events**

- `at_job_scheduled`, `at_job_executed`, `at_job_failed`, `at_job_cancelled`, `at_job_missed`.
- Payload: `job_id`, `summary`, `due`, `status`, `via`.

**Repo and commits**

- The repo is local only, with placeholder GitHub owner, repo, `codeowners`,
  `documentation` and `issue_tracker`. Don't create a GitHub repo.
- Commits use Conventional Commits (the blueprint's commitlint) and **no Claude/AI
  attribution lines of any kind**.
- Test command: `uv run pytest <path> -v`. Full gate: `script/check`, which runs lint,
  types and tests.

## Review Focus

1. **Midnight and noon edges:** "at midnight" or "at 12am" said at 23:59 must resolve to
   00:00 the _next_ day, never a time in the past. "at 12pm" is noon. Test: Task 4,
   `test_midnight_and_noon_edges`.
2. **Jobs left "running" by a crash or restart** must not stay `running` forever. At
   startup, mark them `failed` with the error "Interrupted by restart". Test: Task 6,
   `test_running_job_at_startup_becomes_failed`.
3. **A target removed between scheduling and firing** (entity, script or automation
   deleted) must end the job as `failed` with a readable error, never an unhandled
   exception or a stuck job. Test: Task 7, `test_deleted_target_fails_cleanly`.
4. **Numbers in commands next to a time phrase** must split correctly. In "set the living
   room lights to 50 percent at 6pm", the command keeps "50 percent". In "in 10 minutes
   turn on lamp 2", the command keeps "lamp 2". Test: Task 4, `test_split_keeps_command_numbers`.
5. **A non-English pipeline or `at.schedule` language** must get a clear refusal or a
   skipped registration, never an English parse attempt that guesses. Tests: Task 10 and
   Task 12, both named `test_unsupported_language_refuses`.

---

## File Structure

```text
custom_components/at/
  __init__.py              # async_setup (services, ws, intents), async_setup_entry (manager, triggers, panel, platforms)
  const.py                 # DOMAIN, DISPLAY_NAME, CONF_*, DEFAULT_*, EVENT_*, STORAGE_*, REFUSED_INTENT_TYPES
  data.py                  # AtRuntimeData (manager, pack, unsubscribers); AtConfigEntry type alias
  manifest.json  services.yaml  icons.json  translations/en.json
  lang/__init__.py         # LanguagePack, get_language_pack()
  lang/en.py               # English time words, sentence templates, responses, summary verbs
  core/timeparse.py        # pure: TimeSpec, ResolvedTime, parse_time_text, split_time_and_command, resolve
  core/models.py           # Job, enums, (de)serialization, new_job_id
  core/store.py            # JobStore (HA Store wrapper + migration), prune_history (pure)
  core/manager.py          # JobManager: queue, timers, sweep, startup recovery, subscribe
  core/executor.py         # JobExecutor: runs intent/action jobs
  core/actions.py          # picked-action allowlist, summaries, targets from actions
  core/events.py           # fire_job_event
  ha_internal/recognize.py         # recognize-only adapter
  ha_internal/intents.py           # run a stored intent adapter
  ha_internal/sentence_triggers.py # programmatic sentence-trigger adapter
  voice/scheduling.py      # schedule_command(): time + command → Job or refusal (shared by every text entry point)
  voice/queries.py         # pure list/cancel selection
  voice/intents.py         # AtSchedule / AtList / AtCancel intent handlers
  voice/triggers.py        # registers sentence triggers → intent handlers
  service_actions/__init__.py, schedule.py, list.py, cancel.py, run_now.py, clear_history.py
  sensor/__init__.py, sensor/next_job.py, sensor/pending_jobs.py
  todo/__init__.py
  entity/base.py           # AtEntity (device info)
  websocket_api.py  panel.py  logbook.py  diagnostics.py
  config_flow_handler/...  # confirm step + options flow
  frontend/at-panel.js     # built bundle, committed
frontend/
  package.json tsconfig.json vite.config.ts
  src/at-panel.ts src/api.ts src/format.ts src/types.ts
  src/components/upcoming-table.ts history-table.ts job-details.ts add-job-dialog.ts
  test/format.test.ts
tests/
  conftest.py  core/  voice/  ha_internal/  spike/  test_services.py test_websocket.py test_sensor.py test_todo.py test_config_flow.py test_init.py test_logbook.py
```

---

## Phase 0: Bootstrap

### Task 1: Create the repo from the blueprint and rename it to `at`

**Files:**

- Create: the whole blueprint tree in `/Users/brian/development/at`. Keep the existing
  `docs/superpowers/` and `.superpowers/`.
- Modify: `.gitignore` (add `.superpowers/`), `custom_components/at/manifest.json`

- [ ] **Step 1: Copy in the blueprint.** Clone `https://github.com/jpawlowski/ha-integration-blueprint`
      into a scratch directory. Copy its contents (excluding `.git/`) into the project root
      without overwriting `docs/superpowers/`. Then run `git init -b main`.
- [ ] **Step 2: Run the rename script.** Run
      `./initialize.sh --domain at --title "at (placeholder)" --repo PLACEHOLDER_OWNER/ha-at --author PLACEHOLDER_AUTHOR --dry-run`,
      read the diff it reports, then run it again without `--dry-run`.
      Expected: `custom_components/at/` exists and `grep -r ha_integration_domain .` finds nothing.
- [ ] **Step 3: Set the manifest fields:**
  - `"name": "at (placeholder)"`, `"integration_type": "service"`, `"iot_class": "calculated"`, `"single_config_entry": true`
  - `"dependencies": ["conversation", "intent", "http", "frontend", "panel_custom"]`
  - `"after_dependencies": ["logbook", "todo"]`
  - `codeowners`, `documentation` and `issue_tracker` keep the placeholder values.

  Add `.superpowers/` to `.gitignore`.

- [ ] **Step 4: Bootstrap and check.** Run `script/setup/bootstrap`, then `script/check`.
      Expected: the stock blueprint tests pass.
- [ ] **Step 5: Commit.** `git add -A && git commit -m "chore: initialize at integration from ha-integration-blueprint"`

### Task 2: Strip the polling scaffolding and add a single-instance config flow

**Files:**

- Delete: `custom_components/at/api/`, `coordinator/`, the `binary_sensor/`, `switch/`,
  `select/`, `number/`, `button/` and `fan/` platforms,
  `config_flow_handler/validators/credentials.py`, and the matching tests
- Modify: `__init__.py`, `const.py`, `data.py`, `config_flow_handler/config_flow.py`,
  `config_flow_handler/schemas/*`, `sensor/__init__.py` (empty platform for now),
  `translations/en.json`, `entity/base.py`
- Test: `tests/test_config_flow.py`, `tests/test_init.py`

**Interfaces:**

- Produces:
  - `const.py`: `DOMAIN = "at"`, `DISPLAY_NAME = "at (placeholder)"`, and
    `CONF_GRACE_MINUTES="grace_minutes"` (default 5), `CONF_HISTORY_DAYS="history_days"` (7),
    `CONF_HISTORY_MAX="history_max"` (100), `CONF_PANEL_ADMIN_ONLY="panel_admin_only"` (False),
    `CONF_DEFER_RELATIVE="defer_relative_to_ha"` (False), each with a matching `DEFAULT_*`
  - `data.py`: `@dataclass AtRuntimeData` (fields are added by later tasks) and
    `type AtConfigEntry = ConfigEntry[AtRuntimeData]`
  - `entity/base.py`: `class AtEntity(Entity)`, with `_attr_has_entity_name = True` and one
    service-type `DeviceInfo(identifiers={(DOMAIN, entry.entry_id)}, name=DISPLAY_NAME, entry_type=DeviceEntryType.SERVICE)`

- [ ] **Step 1: Write the failing tests.**
  - `test_user_flow_creates_entry`: the flow shows a confirm form, submitting it creates
    an entry titled `DISPLAY_NAME` with empty data.
  - `test_second_flow_aborts`: once an entry exists, a new flow aborts with
    `single_instance_allowed`.
  - `test_setup_and_unload_entry`: setup returns True and unload returns True.
- [ ] **Step 2: Run the tests.** `uv run pytest tests/test_config_flow.py tests/test_init.py -v`.
      Expected: they fail, because the old credential flow is still there.
- [ ] **Step 3: Replace the config flow with a single `async_step_user` confirm.** No
      reauth or reconfigure. Remove the deleted modules' imports. Leave the options-flow stub
      returning an empty form (Task 22 fills it in).
- [ ] **Step 4: Run the full gate.** `script/check`. Expected: PASS, with no references to
      `api` or `coordinator` left.
- [ ] **Step 5: Commit.** `git commit -am "refactor: strip polling scaffolding, single-instance config flow"`

---

## Phase 1: Spike (go/no-go)

### Task 3: Prove the HA internals that `at` depends on (spec §10)

**Files:**

- Create: `tests/spike/test_ha_internals.py`, `docs/development/SPIKE-FINDINGS.md`

This task writes learning tests against the real HA in the test harness, using
`async_setup_component(hass, "conversation", {})`, a few demo lights and a script,
exposed to Assist with `async_expose_entity`. Each test asserts the behaviour `at` needs.
For each item, record in `SPIKE-FINDINGS.md`:

- the exact module, function and signatures used
- whether it's public or private
- the HA version it was tested on

- [ ] **Step 1: `test_programmatic_sentence_trigger_wildcard_both_orders`.** Register,
      without touching `config/`, the patterns `at {hour} {command}` and `{command} at {hour}`
      (with `hour` as a 1–12 range list and `command` as a wildcard) on the default agent.
      Converse "at 11 turn on the kitchen light" and "turn on the kitchen light at 11".
      Assert the callback runs both times with `command == "turn on the kitchen light"`, and
      that the light did **not** change.
- [ ] **Step 2: `test_recognize_only_returns_intent_without_executing`.** Recognize
      "turn on the kitchen light" with a `device_id` in an area. Assert:
  - the intent type is `HassTurnOn` and the name slot matches
  - the light state is unchanged
  - "turn on the garage light" (not exposed) and "turn on the zzz light" both return a
    distinguishable no-match or no-target result
- [ ] **Step 3: `test_run_stored_intent_later`.** Take the recognized intent type and
      slots from Step 2, serialize them to JSON and back, and run them through HA's intent
      handling with `assistant="conversation"`. Assert the light turns on. Then un-expose the
      light and assert running it again fails.
- [ ] **Step 4: `test_custom_intent_offered_to_llm_api`.** Register a dummy intent handler
      `AtSchedule` with a slot schema and description. Get the Assist LLM API tools and
      assert a tool named `AtSchedule` is present.
- [ ] **Step 5: `test_sentence_trigger_fires_with_prefer_local_llm_pipeline`.** Set up a
      pipeline with a stub non-default conversation agent and `prefer_local_intents=True`.
      Run the text through the pipeline and assert the Step 1 trigger fires.
- [ ] **Step 6: `test_panel_custom_registers`.** Assert `panel_custom.async_register_panel`
      from a custom integration adds the `at` panel to `hass.data["frontend_panels"]`. Record
      in the findings that the frontend picker check (`ha-selector` loading) is manual and
      belongs to Task 21.
- [ ] **Step 7: Run the spike tests.** `uv run pytest tests/spike -v`. Record pass or fail
      per item in `SPIKE-FINDINGS.md`.
- [ ] **Step 8: Go/no-go.**
  - If Step 1, 2 or 3 fails: **stop and report to the author** with what was learned.
  - If Step 4 fails: mark Task 15 deferred.
  - If Step 5 fails: note "LLM tools only with prefer-local" for the docs in Task 23.
- [ ] **Step 9: Commit.** `git add tests/spike docs/development/SPIKE-FINDINGS.md && git commit -m "test: spike HA internals for voice scheduling"`

---

## Phase 2: Core

### Task 4: Language pack and time parser

**Files:**

- Create: `custom_components/at/lang/__init__.py`, `lang/en.py`, `core/__init__.py`, `core/timeparse.py`
- Test: `tests/core/test_timeparse.py`

**Interfaces:**

- Produces:
  - `lang/__init__.py`:
    - `@dataclass(frozen=True) class LanguagePack`, with fields `code: str`,
      `time_patterns`, `day_words`, `period_words`, `weekday_words`, `unit_words`,
      `number_words` (the pack's own regex fragments and word tables; their layout is the
      builder's call), plus `sentences` and `responses` (filled by Tasks 12–14)
    - `get_language_pack(language: str) -> LanguagePack | None`: `"en"` and `"en-*"`
      return the English pack, anything else returns `None`
  - `core/timeparse.py`:
    - `@dataclass(frozen=True) class TimeSpec` with fields:
      - `relative: timedelta | None`
      - `hour: int | None` (0–23 once a meridiem is known, else 1–12) and `minute: int = 0`
      - `meridiem: Literal["am","pm"] | None`
      - `day: Literal["today","tomorrow"] | None`, `weekday: int | None` (0=Mon)
      - `period: Literal["morning","afternoon","evening","night"] | None`
    - `@dataclass(frozen=True) class ResolvedTime`: `due: datetime` (aware UTC), `rolled_over: bool`, `relative: bool`
    - `class TimeParseError(ValueError)`
    - `parse_time_text(text: str, pack: LanguagePack) -> TimeSpec`
    - `split_time_and_command(text: str, pack: LanguagePack) -> tuple[TimeSpec, str]`:
      finds a time phrase only at the **start or end** of the text, and raises
      `TimeParseError` if there's none
    - `resolve(spec: TimeSpec, now: datetime, tz: ZoneInfo) -> ResolvedTime`

- [ ] **Step 1: Write the failing tests.** Use `tz = ZoneInfo("America/Chicago")` unless
      stated otherwise. `now` is 2026-11-17 22:22 local, a Tuesday.

```python
@pytest.mark.parametrize(("text", "expected_local", "rolled"), [
    ("in 20 minutes", "2026-11-17 22:42", False),
    ("in 2 hours", "2026-11-18 00:22", False),
    ("in an hour and a half", "2026-11-17 23:52", False),
    ("in half an hour", "2026-11-17 22:52", False),
    ("in 3 days", "2026-11-20 22:22", False),
    ("at 11pm", "2026-11-17 23:00", False),
    ("at 11 pm", "2026-11-17 23:00", False),
    ("at 6am", "2026-11-18 06:00", True),
    ("at 6:30", "2026-11-18 06:30", True),       # next 6:30 (AM tomorrow beats PM tomorrow)
    ("at 11", "2026-11-17 23:00", False),        # next 11 o'clock is 11 PM today
    ("at 7 o'clock", "2026-11-18 07:00", True),
    ("at noon", "2026-11-18 12:00", True),
    ("at midnight", "2026-11-18 00:00", False),
    ("tomorrow at 7", "2026-11-18 07:00", False),
    ("at 6:30 tonight", "2026-11-18 18:30", True),  # 18:30 today has passed → tomorrow
    ("tomorrow morning at 8", "2026-11-18 08:00", False),
    ("this afternoon at 3", "2026-11-18 15:00", True),
    ("on friday at 8", "2026-11-20 08:00", False),
    ("on tuesday at 11pm", "2026-11-17 23:00", False),   # today, not yet passed
    ("on tuesday at 9am", "2026-11-24 09:00", False),    # today's 9am passed → next week
])
def test_resolve_phrases(text, expected_local, rolled): ...
```

Assert `resolve(parse_time_text(text, EN), NOW, tz).due.astimezone(tz)` equals
`expected_local` and that `rolled_over == rolled`.

- `test_midnight_and_noon_edges`: at 23:59 local, "at midnight" and "at 12am" give
  00:00 the next day (`rolled_over=False`), and "at 12pm" gives 12:00.
- `test_dst_spring_forward_nonexistent_moves_forward`: with
  `now=2026-03-07 23:00 America/Chicago`, "tomorrow at 2:30am" gives 2026-03-08 03:00 local.
- `test_dst_fall_back_ambiguous_uses_first`: with `now=2026-10-31 23:00`, "tomorrow at
  1:30am" gives 2026-11-01 06:30 UTC (CDT, the first occurrence).
- `test_relative_is_exact_duration_across_dst`: with `now=2026-11-01 00:30 local`,
  "in 2 hours" gives `due - now == timedelta(hours=2)`.
- `test_berlin_timezone`: "tomorrow at 7" in Europe/Berlin gives 06:00 UTC in winter.
- `test_split_both_orders`: "at 11pm turn on the master bathroom light" and "turn on the
  master bathroom light at 11pm" both give the command `"turn on the master bathroom light"`.
- `test_split_keeps_command_numbers`: "set the living room lights to 50 percent at 6pm"
  gives the command `"set the living room lights to 50 percent"`, and "in 10 minutes turn
  on lamp 2" gives `"turn on lamp 2"`.
- `test_unparseable_raises`: "at banana", "", "turn on the light" (no time) and "at 25pm"
  all raise `TimeParseError`.
- `test_get_language_pack`: "en" and "en-GB" return the pack, and "de" returns `None`.
- [ ] **Step 2: Run the tests.** `uv run pytest tests/core/test_timeparse.py -v`. Expected: FAIL (import error).
- [ ] **Step 3: Implement the parser.** Use regexes built from the pack, with no date
      libraries. Resolution rules:
  - A clock time with no meridiem or period tries both AM and PM on the anchor day and the
    day after, and picks the earliest candidate that's after `now`.
  - `period` sets the meridiem ("night" and "evening" mean PM, "morning" AM, "afternoon" PM).
  - An explicit day or weekday fixes the date, and the time rolls only by a week for a
    weekday that's already past.
  - `rolled_over=True` when the chosen date is later than the date the phrase named or
    implied ("today" for a bare clock time).
  - Build each candidate with `datetime(..., tzinfo=tz, fold=0)`. If converting to UTC and
    back changes the wall time, the time doesn't exist, so step forward a minute at a time
    to the first valid one.
- [ ] **Step 4: Run the tests.** Same command. Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat(core): deterministic time phrase parser with DST handling"`

### Task 5: Job model and store

**Files:**

- Create: `core/models.py`, `core/store.py`
- Modify: `const.py` (add `STORAGE_KEY="at.jobs"`, `STORAGE_VERSION=1`, `STORAGE_MINOR_VERSION=1`)
- Test: `tests/core/test_models.py`, `tests/core/test_store.py`

**Interfaces:**

- Produces (`core/models.py`):
  - `class JobStatus(StrEnum)`: `PENDING, RUNNING, DONE, FAILED, CANCELLED, MISSED`
  - `class JobKind(StrEnum)`: `INTENT, ACTION`
  - `class Via(StrEnum)`: `VOICE, LLM, PANEL, TODO, SERVICE`
  - `@dataclass IntentSpec`: `type: str`, `slots: dict[str, Any]`, `language: str`,
    `device_id: str | None`, `satellite_id: str | None`
  - `@dataclass Targets`: `entity_ids: list[str]`, `area_ids: list[str]`,
    `floor_ids: list[str]`, `names: list[str]` (spoken target names, for cancel by name)
  - `@dataclass Source`: `via: Via`, `user_id: str | None`, `device_id: str | None`, `agent_id: str | None`
  - `@dataclass Result`: `error: str | None = None`, `cancelled_by: str | None = None`
  - `@dataclass Job` with fields:
    - `id`, `kind`, `status`, `due: datetime`, `created_at: datetime`, `finished_at: datetime | None`
    - `summary: str`, `original_text: str | None`
    - `intent: IntentSpec | None`, `action: list[dict] | None`, `raw_action: bool`
    - `targets: Targets`, `source: Source`, `result: Result`
    - `def to_dict(self) -> dict` and `@classmethod def from_dict(cls, data: dict) -> Job`.
      Datetimes are ISO UTC strings.
  - `new_job_id() -> str`: 8 lowercase hex characters
- Produces (`core/store.py`):
  - `class JobStore`: `__init__(self, hass)`, `async_load(self) -> list[Job]`,
    `async_save(self, jobs: Iterable[Job]) -> None`. It wraps `Store` with a
    `_async_migrate_func` that raises `NotImplementedError` for unknown versions.
  - `prune_history(jobs: list[Job], now: datetime, days: int, max_count: int) -> list[Job]`:
    a pure function that keeps all non-history jobs and the newest `max_count` history jobs
    finished within `days`

- [ ] **Step 1: Write the failing tests.**
  - `test_job_roundtrip`: `Job.from_dict(job.to_dict()) == job` for both an intent job and an action job.
  - `test_new_job_id_format`: matches `^[0-9a-f]{8}$`.
  - `test_store_persists_across_instances`: save two jobs, create a new `JobStore` on the
    same `hass_storage`, load them, and they're equal.
  - `test_store_empty_returns_empty_list`.
  - `test_prune_history_by_age_and_count`: start from 120 done jobs (90 finished within 7
    days, 30 older) plus 3 pending, with `days=7`.
    - With `max_count=100`, the result is 3 pending and the 90 recent history jobs.
    - With `max_count=50`, it's 3 pending and the 50 newest history jobs.
- [ ] **Step 2: Run the tests.** `uv run pytest tests/core/test_models.py tests/core/test_store.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the model and store as specified above.
- [ ] **Step 4: Run the tests.** Same command. Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat(core): job model and versioned store"`

### Task 6: JobManager (queue, timers, sweep, restart recovery, events)

**Files:**

- Create: `core/manager.py`, `core/events.py`, `core/errors.py`
- Modify: `const.py` (`EVENT_JOB_*` constants, `SWEEP_INTERVAL = timedelta(minutes=1)`), `data.py`, `__init__.py`
- Test: `tests/core/test_manager.py`

**Interfaces:**

- Consumes: Task 5's `Job`, `JobStore` and `prune_history`.
- Produces:
  - `core/events.py`: `fire_job_event(hass, event_type: str, job: Job) -> None`, with the
    payload `{job_id, summary, due (ISO), status, via}`
  - `core/manager.py`:
    - `@dataclass ManagerOptions`: `grace: timedelta`, `history_days: int`, `history_max: int`
    - `@dataclass JobChange`: `kind: Literal["added","updated","removed"]`, `job: Job`
    - `class Executor(Protocol)`: `async def async_execute(self, job: Job) -> None`, which raises `JobExecutionError`
  - `core/errors.py`: `JobNotFound`, `JobStateError` and `JobExecutionError(message)`, all
    subclasses of `HomeAssistantError`. Every other task imports these errors from here.
    - `class JobManager(hass, store, executor, options)` with these methods:
      - lifecycle: `async_start()`, `async_stop()`
      - reads: `get(job_id) -> Job`, `pending() -> list[Job]` (sorted by due), `history() -> list[Job]` (newest first)
      - queue changes:
        - `async_add(job) -> Job`: sets `PENDING`, schedules the job, saves, fires the scheduled event
        - `async_cancel(job_id, by: str) -> Job`: only pending jobs, otherwise `JobStateError`
        - `async_cancel_many(job_ids: list[str], by: str) -> list[Job]`
        - `async_set_due(job_id, due) -> Job`: pending jobs only
        - `async_run_now(job_id) -> Job`
        - `async_reschedule(job_id, due) -> Job`: a copy of any job with a new id and due
          date, status pending
        - `async_delete_history(job_ids) -> int`
        - `async_clear_history() -> int`
        - `update_options(options)`
      - `subscribe(cb: Callable[[JobChange], None]) -> Callable[[], None]`
  - `AtRuntimeData.manager: JobManager`. `async_setup_entry` builds the manager from
    entry options (with defaults), then calls `async_start`. Unload calls `async_stop`.

- [ ] **Step 1: Write the failing tests.** Use a `FakeExecutor` that records calls and can
      be set to raise, and the `freezer` fixture together with `async_fire_time_changed`.
  - `test_add_fires_at_due_time`: add a job due in 10 min. At +9 min the executor has not
    been called. At +10 min it has been called once, the status is `DONE`, `finished_at`
    is set, and `at_job_scheduled` and `at_job_executed` fired with the payload keys.
  - `test_executor_error_marks_failed`: the executor raises `JobExecutionError("boom")`.
    The status becomes `FAILED`, `result.error == "boom"`, and `at_job_failed` fires.
  - `test_cancel_pending`: the status becomes `CANCELLED`, `result.cancelled_by` is set,
    the event fires, and the job doesn't run at its due time. Cancelling it again raises
    `JobStateError`.
  - `test_set_due_reschedules`: the job runs at the new time, not the old one.
  - `test_run_now`: the job runs immediately, and its original timer no longer fires.
  - `test_reschedule_copies_history_job`: the copy gets a new id, status pending, and the
    same summary and action, and the original is unchanged.
  - `test_sweep_fires_overdue_after_clock_jump`: freeze, add a job due in 5 min, then
    `freezer.move_to(+10 min)` and fire time changed. The job ran exactly once.
  - `test_restart_restores_pending`: start a manager, add a job, stop it. A new manager on
    the same storage has it pending and it runs at its due time.
  - `test_restart_within_grace_runs_now`: the job was due 3 min before startup, with
    grace 5 min. It runs during `async_start` and `DONE` is recorded.
  - `test_restart_beyond_grace_marks_missed`: the job was due 10 min before startup. It's
    `MISSED`, `at_job_missed` fires, and the executor is not called.
  - `test_running_job_at_startup_becomes_failed`: a stored `RUNNING` job becomes `FAILED`
    with `result.error == "Interrupted by restart"`.
  - `test_two_jobs_same_instant_both_run`.
  - `test_history_pruned_after_finish`: with `history_max=2`, after 3 jobs finish, 2
    remain in history.
  - `test_subscribe_receives_changes`: add, then cancel, gives the callback `added`, then `updated`.
- [ ] **Step 2: Run the tests.** `uv run pytest tests/core/test_manager.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement `JobManager`.**
  - Use one `async_track_point_in_utc_time` per pending job, keyed by id, and cancel it on
    any change.
  - Use one `async_track_time_interval(SWEEP_INTERVAL)` that runs every pending job with
    `due <= utcnow()` that isn't already in flight.
  - Run each job with `hass.async_create_background_task`, so a long action never blocks
    the manager.
  - Before the executor runs, set the job to `RUNNING` and save. Save again after every
    status change.
  - Run `prune_history` after every finish and on start.
  - Call subscriber callbacks synchronously.
- [ ] **Step 4: Run the tests.** Same command. Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat(core): job manager with timers, sweep, restart recovery and events"`

### Task 7: Executor and picked-action rules

**Files:**

- Create: `core/executor.py`, `core/actions.py`, `ha_internal/__init__.py`, `ha_internal/intents.py`
- Modify: `__init__.py` (use the real `JobExecutor`), `lang/en.py` (summary verbs)
- Test: `tests/core/test_executor.py`, `tests/core/test_actions.py`

**Interfaces:**

- Consumes: the `Job` model and the run-stored-intent findings from Task 3 in `SPIKE-FINDINGS.md`.
- Produces:
  - `ha_internal/intents.py`: `async_run_intent(hass, spec: IntentSpec, context: Context) -> None`.
    It runs with `assistant="conversation"` and raises `JobExecutionError(message)` on any
    intent error.
  - `core/executor.py`:
    - `class JobExecutor(hass)` (raises `JobExecutionError` from `core/errors.py`) with `async_execute(job) -> None`:
      - intent jobs go to `async_run_intent`
      - action jobs run through `script.Script(hass, job.action, f"at job {job.id}", DOMAIN).async_run(context=...)`
      - the context is `Context(user_id=job.source.user_id)` if that user still exists,
        otherwise `Context()`
  - `core/actions.py`:
    - `class InvalidAction(HomeAssistantError)`
    - `validate_picked_action(action: list[dict]) -> None`, an allowlist:
      - `homeassistant.turn_on`, `homeassistant.turn_off` and `homeassistant.toggle`, or
        `<domain>.turn_on/turn_off/toggle`, with only a `target` key and no `data`
      - `script.turn_on` with `target` and an optional `data.variables`
      - `automation.trigger` with `target`
      - exactly one step
    - `summarize_action(hass, action: list[dict], pack: LanguagePack) -> str`: for example
      "Turn on Porch Light", "Run Bedtime", "Trigger Morning Routine", or the pack's generic
      "Run action" for raw actions
    - `targets_from_action(hass, action: list[dict]) -> Targets`

- [ ] **Step 1: Write the failing tests.**
  - `test_action_job_runs_service`: an action job turning on `light.porch` (demo/template
    light) turns the light on.
  - `test_script_job_passes_variables`: a script that sets `input_text.x` to `{{ msg }}`
    called with `variables: {msg: "hi"}` sets x to "hi".
  - `test_automation_trigger_job`.
  - `test_intent_job_runs_and_rechecks_exposure`: a stored `HassTurnOn` with a name slot
    turns the light on. Once the light is un-exposed, it raises `JobExecutionError`.
  - `test_deleted_target_fails_cleanly`: a job targeting `script.gone` (removed after the
    job was created) raises `JobExecutionError`, and its message names the target.
  - `test_context_user_missing_falls_back_to_system`.
  - `test_validate_picked_action_allows_shapes`, plus `test_validate_picked_action_rejects`,
    which covers: a `light.turn_on` with `data.brightness`, `shell_command.x`, two steps,
    and a missing target.
  - `test_summarize_action`: "Turn on Porch Light", "Turn off Porch Light", "Toggle Porch
    Light", "Run Bedtime", "Trigger Morning Routine". These use friendly names, and fall
    back to the entity id when an entity has no state.
- [ ] **Step 2: Run the tests.** `uv run pytest tests/core/test_executor.py tests/core/test_actions.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the executor and action rules as specified above. Wrap every
      `HomeAssistantError` or `ServiceNotFound` from script execution in `JobExecutionError`
      with a readable message.
- [ ] **Step 4: Run the tests.** Same command. Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat(core): job executor and picked-action allowlist"`

### Task 8: Logbook descriptions

**Files:**

- Create: `custom_components/at/logbook.py`
- Test: `tests/test_logbook.py`

- [ ] **Step 1: Write the failing test.** `test_logbook_describes_events`: for each of the
      5 events, `async_describe_events` gives the name `DISPLAY_NAME` and a message from the
      pack. Assert these exact strings:
  - "scheduled Turn on Porch Light for 11:00 PM"
  - "ran Turn on Porch Light"
  - "failed Turn on Porch Light: boom"
  - "cancelled Turn on Porch Light"
  - "missed Turn on Porch Light (Home Assistant was down)"

  Times use HA's time zone and a 12-hour clock.

- [ ] **Step 2: Run it.** `uv run pytest tests/test_logbook.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement `async_describe_events(hass, async_describe_event)`.** Put the
      message text in `lang/en.py`. Add an `error` field to the failed-event payload (in
      `core/events.py`) so the failed message can be built.
- [ ] **Step 4: Run it.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat: logbook entries for job events"`

---

## Phase 3: Voice and actions

### Task 9: Recognize-only adapter

**Files:**

- Create: `ha_internal/recognize.py`
- Modify: `const.py` (`REFUSED_INTENT_TYPES`)
- Test: `tests/ha_internal/test_recognize.py`

**Interfaces:**

- Consumes: the recognize-only findings from Task 3.
- Produces:
  - `@dataclass RecognizedCommand`: `intent: IntentSpec`, `targets: Targets`, `summary: str`
    (for example "Turn on Master Bathroom Light", built through the pack)
  - `class RecognizeError(HomeAssistantError)` with
    `code: Literal["no_match","no_target","refused"]` and `message: str`, which is HA's own
    wording when available
  - `async_recognize_command(hass, text: str, *, language: str, device_id: str | None, satellite_id: str | None, context: Context, pack: LanguagePack) -> RecognizedCommand`
  - `REFUSED_INTENT_TYPES`:
    - every intent whose name starts with `At`
    - `HassStartTimer`, `HassCancelTimer`, `HassCancelAllTimers`, `HassIncreaseTimer`,
      `HassDecreaseTimer`, `HassPauseTimer`, `HassUnpauseTimer`, `HassTimerStatus`
    - `HassGetState`, `HassGetWeather`, `HassGetCurrentTime`, `HassGetCurrentDate`,
      `HassNevermind`, `HassRespond`

- [ ] **Step 1: Write the failing tests.**
  - `test_recognizes_turn_on_by_name`: the intent type is `HassTurnOn`, the targets
    include `light.master_bathroom`, and the summary is "Turn on Master Bathroom Light".
  - `test_recognizes_area_and_floor`: "turn off the downstairs lights" resolves to floor targets.
  - `test_uses_satellite_area`: "turn off the lights" with a `device_id` in the Kitchen area gives Kitchen area targets.
  - `test_no_match`: "make it cozy" raises `code="no_match"`.
  - `test_unexposed_is_no_target`: "turn on the garage light" raises `code="no_target"`.
  - `test_refused_intents`: "what's the temperature" and "set a timer for 5 minutes" both
    raise `code="refused"`.
  - `test_does_not_execute`: after all of the above, every light state is unchanged.
- [ ] **Step 2: Run them.** `uv run pytest tests/ha_internal/test_recognize.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the adapter using the spike's API. All private HA imports stay
      in this file.
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat(voice): recognize-only command adapter"`

### Task 10: `schedule_command`, the shared path for scheduling from text

**Files:**

- Create: `voice/__init__.py`, `voice/scheduling.py`
- Modify: `lang/en.py` (confirmation and refusal responses)
- Test: `tests/voice/test_scheduling.py`

**Interfaces:**

- Consumes: Task 4 (`split_time_and_command`, `parse_time_text`, `resolve`), Task 6
  (`JobManager.async_add`), Task 9 (`async_recognize_command`).
- Produces:
  - `@dataclass ScheduleOutcome`: `job: Job`, `speech: str`
  - `class ScheduleRefused(HomeAssistantError)`, with a `speech: str` attribute
  - `async_schedule_command(hass, manager, *, command_text: str, time_text: str | None, language: str, via: Via, user_id: str | None, device_id: str | None, satellite_id: str | None, agent_id: str | None = None, due: datetime | None = None, dry_run: bool = False) -> ScheduleOutcome`
    - When `due` is set, it is used as an absolute time and `command_text` isn't split
      (`at.schedule` with `at`/`delay`, and to-do items with a due field).
    - Otherwise, when `time_text` is None, the time is split out of `command_text`.
    - With `dry_run=True`, it returns the unsaved job (used by the panel preview).
- Response text, exact (`lang/en.py`). The summary's first letter is lowercased inside sentences.
  - absolute, today: `"OK, at 11 PM I'll turn on Master Bathroom Light."`
  - absolute, tomorrow: `"OK, at 6 AM tomorrow I'll turn on Master Bathroom Light."`
  - absolute, within 7 days: `"OK, at 8 AM on Friday I'll turn on Porch Light."`
  - absolute, further out: `"OK, at 8 AM on December 3 I'll …"`
  - relative: `"OK, in 20 minutes, at 10:42 PM, I'll run Bedtime."`
  - times: `"6 AM"`, `"6:30 AM"`, `"12 PM"`, `"12 AM"`
  - unrecognized or refused: `"Sorry, I can only schedule commands I can check right now. Try rephrasing, or schedule a script or scene."`
  - no target: the `RecognizeError.message`
  - bad time: `"Sorry, I didn't understand when."`
  - unsupported language: `"Sorry, scheduling is only available in English for now."`

- [ ] **Step 1: Write the failing tests,** with frozen now 2026-11-17 22:22 Chicago.
  - `test_schedules_absolute_and_confirms`: "turn on the master bathroom light" with "at
    6am" creates a pending intent job due 2026-11-18 06:00 local, and the speech matches
    the "tomorrow" form exactly. `source.via == Via.VOICE`.
  - `test_schedules_relative_and_confirms`: the relative form, exactly.
  - `test_time_split_from_command_text`: `time_text=None` with "turn on the porch light at
    11pm" gives a due time of 23:00.
  - `test_refuses_unrecognized`: "make the living room cozy" raises `ScheduleRefused`
    with the exact refusal text, and no job is added.
  - `test_refuses_bad_time`.
  - `test_dry_run_does_not_add`.
  - `test_unsupported_language_refuses`: `language="de"` raises `ScheduleRefused` with the
    English unsupported-language text, and the parser is never called (patch it and
    assert it isn't called).
- [ ] **Step 2: Run them.** `uv run pytest tests/voice/test_scheduling.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** it as specified above.
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat(voice): shared schedule-from-text pipeline with spoken confirmations"`

### Task 11: Pure list and cancel selection

**Files:**

- Create: `voice/queries.py`
- Modify: `lang/en.py` (list and cancel responses)
- Test: `tests/voice/test_queries.py`

**Interfaces:**

- Produces:
  - `select_for_list(jobs: list[Job], scope: Literal["all","today","tonight","tomorrow"] | None, name: str | None, now: datetime, tz: ZoneInfo) -> list[Job]`.
    "tonight" means from now until 06:00 tomorrow, local.
  - `@dataclass CancelQuery`: `all: bool = False`, `time: TimeSpec | None = None`, `name: str | None = None`
  - `match_for_cancel(jobs: list[Job], query: CancelQuery, now: datetime, tz: ZoneInfo) -> list[Job]`:
    - A time matches jobs whose local due hour and minute equal the resolved spec's (the
      date is ignored, the next one is preferred).
    - A name matches as a case-insensitive substring of `summary` or any of `targets.names`.
    - `all` gives every pending job **except** those with `source.via == Via.SERVICE`.
  - Response text, exact (`lang/en.py`):
    - list: `"Nothing is scheduled."`, or `"{n} scheduled: {item}; {item}; {item}, and {m} more."`
      where an item is `"turn on Porch Light at 11 PM"` (with the tomorrow / on-weekday
      forms from Task 10). The ", and {m} more" part only appears when there are more than 3.
    - cancel one: `"Cancelled: turn on Porch Light at 11 PM."`
    - cancel none: `"I couldn't find a scheduled job matching that."`
    - ambiguous: `"There are 2 jobs for Master Bathroom Light, at 6 AM and 11 PM. Say 'cancel the 6 AM job'."`
    - all: `"Cancelled {n} jobs."`, plus `" {m} jobs created by automations were left alone."` when m > 0

- [ ] **Step 1: Write the failing tests.**
  - `test_list_scopes`: jobs at 23:00 today, 05:00 tomorrow, 09:00 tomorrow and next week.
    "tonight" gives the first two, "tomorrow" the middle two, and "all" all four in due order.
  - `test_list_speech_caps_at_three`.
  - `test_cancel_by_time`.
  - `test_cancel_by_name_substring`.
  - `test_cancel_ambiguous_returns_multiple`.
  - `test_cancel_all_skips_service_jobs`.
  - `test_cancel_speech_variants`: one of each exact string above.
- [ ] **Step 2: Run them.** `uv run pytest tests/voice/test_queries.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** it as specified above.
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat(voice): list and cancel selection with spoken responses"`

### Task 12: Intent handlers (AtSchedule, AtList, AtCancel)

**Files:**

- Create: `voice/intents.py`
- Modify: `__init__.py` (register them in `async_setup_entry`, and remove them on unload)
- Test: `tests/voice/test_intents.py`

**Interfaces:**

- Consumes: Tasks 10 and 11.
- Produces:
  - Intent types `INTENT_SCHEDULE = "AtSchedule"`, `INTENT_LIST = "AtList"` and `INTENT_CANCEL = "AtCancel"`.
  - Slot schemas:
    - AtSchedule: `time: str` and `command: str`, both required
    - AtList: `scope: str` and `name: str`, both optional
    - AtCancel: `time: str`, `name: str` and `all: bool`, all optional
  - Descriptions for LLMs. AtSchedule's, exact: `"Schedule a Home Assistant voice command
to run once at a later time. Pass the user's time phrase verbatim in 'time' (e.g. 'at
6am', 'in 20 minutes', 'tomorrow at 7') and the command as a plain sentence in
'command' (e.g. 'turn on the porch light'). Never run the command yourself."`
  - The handlers read the manager from the single loaded entry.
  - `via` is `Via.LLM` when the call came through the LLM API tool, and `Via.VOICE`
    otherwise. _(Builder's call: detect the LLM through `intent_obj.platform` or
    `intent_obj.assistant`, whichever Task 3 showed to be reliable.)_
  - The response is a speech `IntentResponse`. A `ScheduleRefused` becomes an error
    response carrying its speech.

- [ ] **Step 1: Write the failing tests.**
  - `test_at_schedule_intent_creates_job`: `intent.async_handle(hass, "test", "AtSchedule", {"time": {"value": "at 11pm"}, "command": {"value": "turn on the porch light"}})`
    gives the exact confirmation speech and one pending job.
  - `test_at_schedule_intent_refusal_is_error_response`.
  - `test_at_list_intent_speech`.
  - `test_at_cancel_intent_all_skips_service`.
  - `test_unsupported_language_refuses`: handling AtSchedule with `language="de"` gives
    the unsupported-language speech and adds no job.
- [ ] **Step 2: Run them.** `uv run pytest tests/voice/test_intents.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the three handlers.
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat(voice): AtSchedule/AtList/AtCancel intents"`

### Task 13: Sentence triggers for the built-in agent

**Files:**

- Create: `ha_internal/sentence_triggers.py`, `voice/triggers.py`
- Modify: `lang/en.py` (`sentences`), `__init__.py`
- Test: `tests/voice/test_triggers.py`

**Interfaces:**

- Consumes: Task 3's trigger findings and Task 12's handlers.
- Produces:
  - `ha_internal/sentence_triggers.py`:
    - `@dataclass TriggerInput`: `sentence: str`, `wildcards: dict[str, str]`,
      `language: str`, `device_id: str | None`, `satellite_id: str | None`, `context: Context`
    - `async_register_sentence_trigger(hass, sentences: list[str], callback: Callable[[TriggerInput], Awaitable[str]]) -> Callable[[], None]`
  - `voice/triggers.py`: `async_setup_triggers(hass, pack: LanguagePack, *, defer_relative: bool) -> Callable[[], None]`.
    It registers three groups (schedule, list, cancel) and leaves out the relative-time
    schedule templates when `defer_relative` is set.
  - `pack.sentences` groups: `schedule_absolute`, `schedule_relative`, `list` and
    `cancel`. They must cover every sentence in the test below. Time pieces use range
    lists, and the command is the `{command}` wildcard.
  - The schedule callback gets the time text as `sentence` with `wildcards["command"]`
    removed, then calls the `AtSchedule` handler. List and cancel map wildcards or lists
    onto their intent slots.

- [ ] **Step 1: Write the failing tests.** Use `conversation.async_converse` against the
      built-in agent, with an exposed `light.master_bathroom` and `script.bedtime`.

```python
@pytest.mark.parametrize("sentence", [
    "at 11pm turn on the master bathroom light",
    "turn on the master bathroom light at 6am",
    "at 6:30 tonight turn on the master bathroom light",
    "tomorrow at 7 turn on the master bathroom light",
    "turn on the master bathroom light tomorrow at 7",
    "on friday at 8 turn on the master bathroom light",
    "in 30 minutes run the bedtime script",
    "run the bedtime script in 30 minutes",
    "in an hour and a half turn on the master bathroom light",
])
def test_schedule_sentences(sentence): ...  # response starts with "OK, ", one pending job, light unchanged
```

- `test_list_sentences`: "what's scheduled", "what's scheduled for tonight", "what's
  scheduled for tomorrow", "what is scheduled" and "what's scheduled for the master
  bathroom light" each give list speech. The last one lists only that light's jobs.
- `test_cancel_sentences`: "cancel the 6am job", "cancel the job at 6", "cancel the
  master bathroom light", "cancel everything scheduled" and "cancel all jobs".
- `test_defer_relative_leaves_relative_to_ha`: with `defer_relative=True`, "turn on the
  master bathroom light in 5 minutes" creates **no** `at` job, while "at 11pm …" still does.
- `test_plain_timer_not_captured`: "set a timer for 5 minutes" creates no `at` job.
- `test_unrecognized_command_refusal_speech`: "at 10 make the living room cozy" gives
  the exact refusal text.
- [ ] **Step 2: Run them.** `uv run pytest tests/voice/test_triggers.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the adapter, the templates and the registration. Keep the
      private imports in `ha_internal/sentence_triggers.py`.
- [ ] **Step 4: Run them.** Expected: PASS. Also run `uv run pytest tests/spike -v`, which
      should still pass.
- [ ] **Step 5: Commit.** `git commit -m "feat(voice): built-in agent sentence triggers for schedule, list and cancel"`

### Task 14: Actions (services)

**Files:**

- Create: `service_actions/schedule.py`, `list.py`, `cancel.py`, `run_now.py`, `clear_history.py`
- Modify: `service_actions/__init__.py` (register in `async_setup`), `services.yaml`, `translations/en.json`
- Test: `tests/test_services.py`

**Interfaces:**

- Consumes: Tasks 6, 7 and 10.
- Produces the services, all with `SupportsResponse` as shown:
  - `at.schedule`
    - Fields: exactly one of `command` (str) or `action` (action selector), plus exactly
      one of `at` (datetime), `delay` (duration) or `when` (str), and an optional `name`.
    - Response (`ONLY|OPTIONAL`): `{job_id, due, summary}`.
    - A `command` job uses `async_schedule_command(time_text=when, due=<from at or now+delay>, via=Via.SERVICE)`.
    - An `action` job sets `raw_action=True`. It is admin-only when
      `call.context.user_id` is set and the user isn't an admin (`Unauthorized`).
  - `at.list`: fields `status` (list, optional), `start` and `end` (datetime, optional).
    Response (`ONLY`): `{pending: [job dict], history: [job dict]}`.
  - `at.cancel`: fields `job_id` (str or list) or `all: true`. The service form of `all`
    cancels **every** pending job, including service-created ones; only the voice
    "cancel everything" skips them. Response: `{cancelled: [ids]}`.
  - `at.run_now`: field `job_id`. For a `raw_action` job, a non-admin user gets `Unauthorized`.
  - `at.clear_history`. Response: `{removed: n}`.

- [ ] **Step 1: Write the failing tests.**
  - `test_schedule_command_with_when`.
  - `test_schedule_action_with_delay`.
  - `test_schedule_requires_exactly_one_time_field`: both `at` and `delay` raise `vol.Invalid`.
  - `test_schedule_raw_action_non_admin_unauthorized`.
  - `test_schedule_raw_action_from_automation_context_ok`: no user, so it's allowed.
  - `test_list_response`.
  - `test_cancel_by_id_and_all`.
  - `test_run_now_raw_action_non_admin_unauthorized`.
  - `test_clear_history`.
- [ ] **Step 2: Run them.** `uv run pytest tests/test_services.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the handlers following the blueprint's `service_actions/` pattern.
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat: at.schedule/list/cancel/run_now/clear_history actions"`

### Task 15: LLM tool exposure (skip if the spike's Step 4 failed)

**Files:**

- Test: `tests/voice/test_llm_api.py`
- Modify: `voice/intents.py` (only if the descriptions or slot schemas need adjusting)

- [ ] **Step 1: Write the failing test.** `test_at_intents_exposed_as_llm_tools`: the
      Assist LLM API tools include `AtSchedule`, `AtList` and `AtCancel` with their
      descriptions. Calling the `AtSchedule` tool with `{"time": "in 20 minutes", "command": "turn on the porch light"}`
      creates a job with `via == Via.LLM`, and the tool result includes the confirmation speech.
- [ ] **Step 2: Run it.** `uv run pytest tests/voice/test_llm_api.py -v`.
- [ ] **Step 3: Adjust** the slot schemas and descriptions until it passes.
- [ ] **Step 4: Run it.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "test(voice): AtSchedule/AtList/AtCancel available as LLM tools"`

---

## Phase 4: Entities

### Task 16: Sensors

**Files:**

- Create: `sensor/next_job.py`, `sensor/pending_jobs.py`
- Modify: `sensor/__init__.py`, `translations/en.json`, `icons.json`, `__init__.py` (forward the `sensor` and `todo` platforms)
- Test: `tests/test_sensor.py`

**Interfaces:**

- Consumes: `JobManager.subscribe` and `pending()`.
- Produces:
  - `sensor.at_next_job` (translation key `next_job`): `device_class=TIMESTAMP`, with
    state equal to the earliest pending due time or `None`, and attributes `job_id` and `summary`.
  - `sensor.at_pending_jobs` (key `pending_jobs`): an int state, with attribute `jobs`,
    a list of `{id, due, summary}`.

- [ ] **Step 1: Write the failing tests.** `test_next_job_sensor_tracks_queue` covers
      empty → unknown, then the earliest job after adding two, then the next one once the
      earliest is cancelled. Also `test_pending_jobs_sensor_count_and_attributes`.
- [ ] **Step 2: Run them.** `uv run pytest tests/test_sensor.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** them using `AtEntity`. Both subscribe in `async_added_to_hass`.
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat: next-job and pending-jobs sensors"`

### Task 17: To-do entity

**Files:**

- Create: `todo/__init__.py`
- Test: `tests/test_todo.py`

**Interfaces:**

- Consumes: `JobManager` and `async_schedule_command`.
- Produces `todo.at_scheduled` (translation key `scheduled`) with these features:
  `CREATE_TODO_ITEM | DELETE_TODO_ITEM | UPDATE_TODO_ITEM | SET_DUE_DATETIME_ON_ITEM | SET_DESCRIPTION_ON_ITEM`.
  - **Items:**
    - Pending jobs come first, sorted by due, with `uid=job.id`, `status=NEEDS_ACTION`,
      `due=job.due` and `summary=job.summary`.
    - History jobs follow, newest first, with `status=COMPLETED` and `description` holding
      the status and result ("Done", "Failed: `<error>`", "Missed", "Cancelled").
  - **Create:** `async_schedule_command(command_text=item.summary, time_text=None, via=Via.TODO, ...)`.
    If the summary has no time phrase and `item.due` is set, use `item.due` as an absolute
    time. A `ScheduleRefused` is re-raised as `HomeAssistantError(speech)`.
    The user comes from `self._context`.
  - **Update:**
    - Changing `due` on a pending item calls `async_set_due`.
    - Setting `status` to COMPLETED on a pending item calls `async_run_now`, which follows
      the raw-action admin rule.
    - Changing the summary raises `HomeAssistantError("Cancel and re-add to change a job")`.
  - **Delete:** a pending job is cancelled, and a history job goes through `async_delete_history`.

- [ ] **Step 1: Write the failing tests.**
  - `test_items_reflect_queue_and_history`.
  - `test_add_item_with_time_in_text`: "turn on the porch light at 11pm".
  - `test_add_item_with_due_field`.
  - `test_add_item_unrecognized_raises`.
  - `test_delete_pending_cancels`.
  - `test_change_due_reschedules`.
  - `test_complete_pending_runs_now`.
  - `test_summary_edit_rejected`.
- [ ] **Step 2: Run them.** `uv run pytest tests/test_todo.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** it as specified above.
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat: to-do entity for the job queue"`

---

## Phase 5: Panel

### Task 18: WebSocket API

**Files:**

- Create: `custom_components/at/websocket_api.py`
- Modify: `__init__.py` (register in `async_setup`)
- Test: `tests/test_websocket.py`

**Interfaces:**

- Consumes: `JobManager`, `async_schedule_command`, `validate_picked_action` and `summarize_action`.
- Produces these commands. Job objects on the wire are `Job.to_dict()`.

| type               | params                                                         | result                                                                      |
| ------------------ | -------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `at/subscribe`     | –                                                              | an event `{"snapshot": {pending, history}}`, then `{"change": {kind, job}}` |
| `at/parse`         | `text`                                                         | `{ok: true, summary, due}` or `{ok: false, message}`. Never creates a job.  |
| `at/schedule`      | `text`, **or** `action` + one of `due` (ISO) / `delay_seconds` | `{job}`                                                                     |
| `at/cancel`        | `job_ids: list`                                                | `{cancelled: [ids]}`                                                        |
| `at/run_now`       | `job_id`                                                       | `{job}`                                                                     |
| `at/reschedule`    | `job_id`, `due`                                                | `{job}` (a new copy)                                                        |
| `at/clear_history` | –                                                              | `{removed}`                                                                 |
| `at/info`          | –                                                              | `{is_admin, panel_admin_only, language_supported}`                          |

- **Who can schedule an `action`:**
  - Admins can send any action. If the action passes `validate_picked_action`, it's
    saved with `raw_action=False`; otherwise it's saved with `raw_action=True`.
  - For non-admins, the action must pass `validate_picked_action`, otherwise the command
    returns `unauthorized`.
- `at/run_now` and `at/reschedule` of a `raw_action` job require an admin.

- [ ] **Step 1: Write the failing tests,** using the `hass_ws_client` and `hass_admin_user`
      or `hass_read_only_user` fixtures.
  - `test_subscribe_snapshot_then_changes`.
  - `test_parse_preview_no_job`.
  - `test_parse_refusal_message`.
  - `test_schedule_text`.
  - `test_schedule_picked_action_non_admin_ok`.
  - `test_schedule_raw_action_non_admin_unauthorized`.
  - `test_schedule_raw_action_admin_ok_sets_raw_flag`.
  - `test_cancel_any_users_job`: a job created by an admin can be cancelled by a non-admin.
  - `test_run_now_raw_action_non_admin_unauthorized`.
  - `test_reschedule_copy`.
  - `test_info_flags`.
- [ ] **Step 2: Run them.** `uv run pytest tests/test_websocket.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the commands with `@websocket_api.websocket_command` and
      `@websocket_api.async_response`. The subscribe command unsubscribes when the
      connection closes.
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat: websocket API for the panel"`

### Task 19: Frontend toolchain, panel shell and registration

**Files:**

- Create: `frontend/package.json`, `tsconfig.json`, `vite.config.ts`, `src/at-panel.ts`,
  `src/api.ts`, `src/types.ts`, `src/format.ts`, `test/format.test.ts`,
  `custom_components/at/panel.py`, `custom_components/at/frontend/at-panel.js` (built output)
- Modify: `mise.toml` (add `node = "22"`), `.pre-commit-config.yaml` (exclude the built
  bundle from Prettier and codespell), `__init__.py` (call `async_register_panel` in setup
  entry and `async_remove_panel` on unload), `script/` (add `script/build-frontend`, which
  runs `npm --prefix frontend ci && npm --prefix frontend run build`)
- Test: `frontend/test/format.test.ts`, `tests/test_panel.py`

**Interfaces:**

- Produces:
  - `src/types.ts`: a `Job` TypeScript interface mirroring `Job.to_dict()`.
  - `src/api.ts`: `subscribeJobs(hass, cb)`, `parse(hass, text)`, `schedule(hass, payload)`,
    `cancel(hass, ids)`, `runNow(hass, id)`, `reschedule(hass, id, due)`,
    `clearHistory(hass)` and `info(hass)`, all thin wrappers around `hass.connection`.
  - `src/format.ts`:
    - `formatCountdown(dueMs: number, nowMs: number): string` gives `"27:41"` under 1 h and `""` otherwise
    - `formatWhen(due: Date, now: Date, locale: string, timeZone: string): string` gives
      `"11:00 PM"` today, `"Tue 6:00 AM"` within 7 days, and `"Dec 3, 8:00 AM"` otherwise
  - `panel.py`:
    - `async_register_panel(hass, entry)` registers the static path
      `/at_static` → `custom_components/at/frontend` and calls `panel_custom.async_register_panel`
      with: `frontend_url_path="at"`, `webcomponent_name="at-panel"`,
      `module_url=f"/at_static/at-panel.js?v={VERSION}"`, `sidebar_title=DISPLAY_NAME`,
      `sidebar_icon="mdi:clock-start"`, and `require_admin=options[CONF_PANEL_ADMIN_ONLY]`
    - `async_remove_panel(hass)`
  - `at-panel` custom element: a Lit element with `hass`, `narrow` and `panel` properties
    that renders the header (title, tabs, "+ Add job", ⋮ menu) and an empty body.

- [ ] **Step 1: Write the failing tests.**
  - Vitest `format.test.ts` covers `formatCountdown(now+1661000, now) === "27:41"`,
    `formatCountdown(now+3_600_001, now) === ""`, and the three `formatWhen` cases in
    `America/Chicago` and `en-US`.
  - Pytest `test_panel_registered_and_removed`: after setup `"at"` is in
    `hass.data["frontend_panels"]` with `require_admin` False, and after unload it's gone.
  - Pytest `test_panel_require_admin_option`.
- [ ] **Step 2: Run them.** `npm --prefix frontend test` and `uv run pytest tests/test_panel.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the toolchain (Vite library mode, a single ES module output at
      `../custom_components/at/frontend/at-panel.js`, with Lit bundled in), `format.ts`, the
      `api.ts` wrappers, the panel shell and `panel.py`.
- [ ] **Step 4: Build and test.** Run `script/build-frontend`, then both test commands. Expected: PASS.
- [ ] **Step 5: Manual check.** Run `script/develop` and open the sidebar entry. The header
      renders and follows HA's light and dark themes.
- [ ] **Step 6: Commit.** `git commit -m "feat(panel): frontend toolchain, panel shell and registration"`

### Task 20: Upcoming and History tabs

**Files:**

- Create: `frontend/src/components/upcoming-table.ts`, `history-table.ts`, `job-details.ts`
- Modify: `frontend/src/at-panel.ts`, `frontend/test/` (add `panel-state.test.ts`)
- Test: `frontend/test/panel-state.test.ts`

**Interfaces:**

- Produces `src/state.ts`:
  - `applyChange(state: {pending: Job[], history: Job[]}, change: {kind, job}): {pending, history}`,
    a pure function that moves jobs between lists by status and keeps the sort orders
    (pending by due ascending, history by `finished_at` descending)

**What the panel shows (spec §7.5)**

- **Upcoming** columns: When, which is `formatCountdown` when non-empty, otherwise
  `formatWhen`, ticking every second; Job; Source (🎙 device name, 🖱 user name, or ⚙
  automation); and the actions ▶ (run now) and ✕ (cancel).
  - ▶ is hidden for `raw_action` jobs when `info.is_admin` is false.
  - Clicking a row opens `job-details`, showing the stored action as YAML or the intent
    type and slots, the creator, the created time and the id.
- **History** columns: status icon (✓ / ✗ / ⚠ / ⊘), time, job, and result or error.
  There's a status filter chip row and a Re-schedule action, which opens a date-time
  input and calls `reschedule`.
- **⋮ menu:** "Cancel all" (with an inline confirm, not `window.confirm`) and "Clear history".

- [ ] **Step 1: Write the failing tests.**
  - `applyChange` for added-pending, updated pending to done (moves to history at the
    top), cancelled, and removed (deleted history).
- [ ] **Step 2: Run them.** `npm --prefix frontend test`. Expected: FAIL.
- [ ] **Step 3: Implement** `state.ts` and the components. Use HA theme CSS variables,
      and HA elements only if they're already loaded (`customElements.get`). Otherwise use
      plain Lit markup.
- [ ] **Step 4: Build and test.** `script/build-frontend && npm --prefix frontend test`.
      Expected: PASS.
- [ ] **Step 5: Manual check** in `script/develop`:
  - Schedule a job via Developer Tools → Actions. It appears without a reload, and the
    countdown ticks.
  - Cancel moves it to History with ⊘.
  - Run now runs it and it shows ✓.
- [ ] **Step 6: Commit.** `git commit -m "feat(panel): upcoming and history tabs with live updates"`

### Task 21: Add job dialog

**Files:**

- Create: `frontend/src/components/add-job-dialog.ts`
- Modify: `frontend/src/at-panel.ts`
- Test: `frontend/test/add-job.test.ts`

**Interfaces:**

- Produces `src/add-job.ts`:
  - `buildPickedAction(p: {targetEntityIds: string[], verb: "turn_on"|"turn_off"|"toggle"} | {script: string, variables?: Record<string, unknown>} | {automation: string}): object[]`.
    It must produce exactly the shapes `validate_picked_action` accepts (Task 7).
  - `quickDue(chip: "+15m"|"+1h", now: Date): {delay_seconds: number}`.

**Dialog modes**

- **Type it:** a text field, with `parse` debounced at 300 ms. It shows the preview
  "Turn on Porch Light · today 11:00 PM ✓" or the refusal message. Submitting calls
  `schedule({text})`.
- **Pick it:**
  - a target picker (entity) and an action picker (turn on / turn off / toggle / run
    script with a variables YAML box / trigger automation)
  - when: the chips +15m and +1h, or a datetime-local input
  - submitting calls `schedule({action, due | delay_seconds})`
- **Raw YAML:** a textarea for an action list, shown only when `info.is_admin`.
- **Pickers:** try HA's `ha-selector` (`{entity: {}}` and `{target: {}}`). If
  `customElements.get("ha-selector")` is undefined after the panel loads, fall back to a
  plain `<select>` of `hass.states`, filtered by domain.

- [ ] **Step 1: Write the failing tests.**
  - `buildPickedAction` gives the three shapes exactly, for example
    `[{action: "homeassistant.turn_on", target: {entity_id: ["light.porch"]}}]`.
  - `quickDue` gives 900 and 3600.
- [ ] **Step 2: Run them.** `npm --prefix frontend test`. Expected: FAIL.
- [ ] **Step 3: Implement** the helpers and the dialog.
- [ ] **Step 4: Build and test.** `script/build-frontend && npm --prefix frontend test`. Expected: PASS.
- [ ] **Step 5: Manual check** in `script/develop`:
  - Type "turn on the porch light at 11pm": the preview shows, and Add creates the job.
  - Pick light, Turn on, +15m creates a job.
  - As a non-admin user the Raw YAML tab is hidden.
  - Record whether `ha-selector` loaded, or the fallback was used, in `SPIKE-FINDINGS.md`.
- [ ] **Step 6: Commit.** `git commit -m "feat(panel): add job dialog with type-it and pick-it modes"`

---

## Phase 6: Polish

### Task 22: Options flow

**Files:**

- Modify: `config_flow_handler/options_flow.py`, `config_flow_handler/schemas/options.py`,
  `translations/en.json`, `__init__.py` (an update listener that reloads the entry)
- Test: `tests/test_config_flow.py`

- [ ] **Step 1: Write the failing tests.**
  - `test_options_flow_saves_values`: grace 10, history days 3, history max 20, panel
    admin-only true, defer relative true. These are stored in `entry.options`.
  - `test_options_reload_applies_defer_relative`: after setting defer relative, "turn on
    the master bathroom light in 5 minutes" creates no `at` job.
  - `test_options_validation`: grace from 0 to 1440, days from 1 to 365, max from 1 to 10000.
- [ ] **Step 2: Run them.** `uv run pytest tests/test_config_flow.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the options schema with `NumberSelector` and `BooleanSelector`,
      and the reload-on-update listener.
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat: options flow for grace window, history, panel access and relative-time handoff"`

### Task 23: Diagnostics, docs, HACS metadata and the release gate

**Files:**

- Modify: `diagnostics.py`, `hacs.json`, `README.template.md` / `README.md`, `docs/user/`,
  `info.md` (if the blueprint has one), `translations/en.json` (completeness)
- Test: `tests/test_diagnostics.py`

- [ ] **Step 1: Write the failing test.** `test_diagnostics_contents`: the output contains
      the options, the counts by status, the language support flag, and the `ha_internal`
      probe results. Each probe reports whether its adapter imported cleanly. It must not
      contain `user_id` values; those are redacted.
- [ ] **Step 2: Run it.** `uv run pytest tests/test_diagnostics.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement diagnostics, then write the user docs:**
  - installation
  - voice phrases (the Task 13 list)
  - the panel
  - the to-do and sensors
  - the actions, with examples
  - the options, including the relative-time handoff
  - LLM agents (plus the prefer-local note if the spike's Step 5 failed)
  - known limits: English only; commands must be ones the built-in agent understands
- [ ] **Step 4: Full gate.** Run `script/build-frontend && script/check && npm --prefix frontend test`.
      Expected: all PASS, with no Pyright errors and no Ruff findings.
- [ ] **Step 5: Commit.** `git commit -m "docs: user docs, diagnostics and HACS metadata"`
