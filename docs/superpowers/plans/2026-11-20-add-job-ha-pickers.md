# Add job dialog with Home Assistant's pickers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let any user schedule any single action from **Pick it** with HA's `ha-service-control`, give admins HA's
sequence editor in place of **Raw**, and replace the five-verb allowlist with the Home Assistant permission pattern.

**Architecture:** The backend's `validate_picked_action` becomes a "single literal step" rule; `raw_action` is set
when the rule fails **or** the scheduler is an admin or absent, and the existing `raw_action` checks on run now,
reschedule and the to-do item stay as they are. The frontend loads `ha-service-control` and `ha-selector` lazily on
first dialog open through the existing route-loading trick, wraps each in a small tab component that falls back to
today's controls, and both tabs report a one-or-more-step action list to the dialog.

**Tech Stack:** Python 3.14, Home Assistant (installed frontend 20260930.5), pytest-homeassistant-custom-component;
TypeScript 5.9, Lit 3.3, Vite 8, Vitest 5 with happy-dom.

**Spec:** [`docs/superpowers/specs/2026-11-20-add-job-ha-pickers-design.md`](../specs/2026-11-20-add-job-ha-pickers-design.md)

## Global Constraints

- Single-step rule: exactly one step; step keys only `action` (any `domain.service`), optional `target`, optional
  `data`; target keys only `entity_id`, `area_id`, `device_id`, `floor_id`, `label_id` with explicit string ids;
  `all` / `none` rejected; no templates anywhere in `data` at any depth; the same target keys inside `data` get the
  target checks.
- `raw_action = not passes_rule or scheduler is admin or scheduler is None`. Applies to the websocket `at/schedule`,
  the `at.schedule` action and reschedule copies. Stored jobs are not migrated.
- A job whose stored `user_id` no longer resolves fails with "The user who scheduled this job no longer exists". No
  stored user → runs with an empty `Context()` as today.
- Strings: English only, in `custom_components/at/lang/en.py` (messages) and `translations/en.json`; never touch
  another language file.
- No change to the job's stored shape, to Type it, the When section, voice, or the LLM tools.
- Python: `script/lint`, `script/type-check`, `script/test`. Frontend: `npm --prefix frontend test`,
  `npm --prefix frontend run typecheck`, `script/build-frontend` (the built `custom_components/at/frontend/at-panel.js`
  is committed).
- Commit only when the developer asks (`AGENTS.md`). Each task ends at a green state; the commit step names the
  message to offer.

## Review Focus

1. **Admin reschedules a non-admin's job.** The copy runs as the admin (`Source.user_id` is the rescheduler), so it
   must be flagged `raw_action=True`, or a non-admin could then run it with admin rights. Test in Task 2.
2. **Template hidden in nested data**, such as `data: {"rgb_color": ["{{ 1 }}", 0, 0]}` or
   `data: {"message": {"title": "{% if %}"}}`, must make the action admin-only. Test in Task 1.
3. **An action with no target at all** (`persistent_notification.create` with `data.message`) must pass the
   single-step rule for a non-admin. Test in Task 1.
4. **HA elements arrive after the dialog first rendered the fallback.** A tab must not swap controls under a user
   halfway through; it decides once per dialog open. Test in Task 6.
5. **`ha-service-control` emits a value with no action yet** (the user cleared the picker). **Add** must go back to
   disabled rather than send `{action: undefined}`. Test in Task 6.

---

### Task 0: Spike — do HA's elements work inside the panel? (throwaway, developer at a browser)

No browser runs in this container, so this task needs the developer. It produces findings, not code.

**Files:**

- Modify (throwaway, then reverted): `frontend/src/components/add-job-dialog.ts`
- Modify (kept): `docs/development/SPIKE-FINDINGS.md` — the pending Task 21 entry

- [ ] **Step 1:** On a scratch branch, render `<ha-service-control .hass narrow>` in place of the Pick it selects and
      `<ha-selector .hass .selector=${{ action: {} }}>` in place of the Raw textarea; log every `value-changed` detail
      to the console. Before opening, try in order: (1) load the `developer-tools` panel route through
      `partial-panel-resolver._getRoutes` and its `routerOptions.routes.action`; (2) the config panel's
      `automation` route and its `edit` sub-route. Log `customElements.get()` for `ha-service-control`,
      `ha-selector`, `ha-selector-action`, `ha-target-picker` after each.
- [ ] **Step 2:** `script/build-frontend`, start the dev instance per `at-live-test`, and ask the developer to open
      the panel and report: which load made each tag defined; whether picking `light.turn_on` narrows the target
      picker to lights and shows brightness/colour fields; whether its popups (action list, target picker, colour
      picker) open above our dialog and take focus; whether the sequence editor's **Add action** menu and YAML view
      work; the exact `value-changed` detail shapes.
- [ ] **Step 3:** Record the answers under the Task 21 entry in `SPIKE-FINDINGS.md`, replacing "pending". Note the
      decision each answer drives: route list for Task 5; `ha-dialog` shell needed or not (Task 6 Step 5); approach
      B for Pick it if `ha-service-control` fails (the spec's fallback approach — stop and re-plan Task 6 if so).
- [ ] **Step 4:** Revert the scratch dialog changes (`git checkout frontend/src custom_components/at/frontend`).
      Offer: `docs: record whether HA's action pickers load in the panel`.

### Task 1: The single-step rule

**Files:**

- Modify: `custom_components/at/core/actions.py:25-115` (`_TOGGLES`, `_SCRIPT_RUN`, `_AUTOMATION_TRIGGER`,
  `_check_data`, `validate_picked_action`)
- Modify: `custom_components/at/lang/en.py:407-418`
- Test: `tests/core/test_actions.py`, `tests/test_picked_shapes.py`

**Interfaces:**

- Produces: `validate_picked_action(action: list[dict[str, Any]], pack: LanguagePack | None = None) -> None` — same
  name and exceptions (`InvalidAction` for bad shape, `ActionNotAllowed` for allowed shape but admin-only content).
  Templates, `all`/`none`, extra step keys and more than one step raise `ActionNotAllowed`.

- [ ] **Step 1: Write the failing tests** — extend the two parametrized tests in `tests/core/test_actions.py`:

```python
# allowed (test_validate_picked_action_allows_shapes)
[{"action": "climate.set_temperature", "target": {"area_id": "living_room"}, "data": {"temperature": 21}}],
[{"action": "persistent_notification.create", "data": {"message": "Hi", "title": "At"}}],
[{"action": "light.turn_on", "target": {"entity_id": ["light.a"]}, "data": {"rgb_color": [255, 0, 0]}}],
[{"action": "notify.notify", "data": {"message": "x", "data": {"tag": "a"}}}],
# rejected with ActionNotAllowed (new test_validate_picked_action_admin_only)
[{"action": "light.turn_on", "target": {"entity_id": "light.a"}, "data": {"rgb_color": ["{{ 1 }}", 0, 0]}}],
[{"action": "notify.notify", "data": {"message": {"title": "{% if x %}y{% endif %}"}}}],
[{"action": "light.turn_off", "data": {"entity_id": "all"}}],
[{"action": "light.turn_off", "target": {"entity_id": "all"}}],
[{"action": "light.turn_on", "target": {"entity_id": "light.a"}, "continue_on_error": True}],
[{"action": "light.turn_on", "target": {"entity_id": "light.a"}}, {"delay": 5}],
[{"delay": 5}],
# rejected with InvalidAction
[{"action": "light.turn_on", "data": ["not", "a", "mapping"]}],
[{"action": "light.turn_on", "target": {"entity_id": []}}],
```

Remove the old cases that assert `shell_command.run` or `data` other than `variables` is refused. Keep
`tests/test_picked_shapes.py` passing unchanged except that its `shell_command.run` rejection case becomes a
template-in-data case.

- [ ] **Step 2:** Run `script/test tests/core/test_actions.py tests/test_picked_shapes.py` — expect the new cases to
      FAIL.
- [ ] **Step 3: Implement.** Drop `_TOGGLES`, `_SCRIPT_RUN`, `_AUTOMATION_TRIGGER` and `_check_data`. Allowed step
      keys `{"action", "target", "data"}`; `target` optional but `_check_target` when present; `data` must be a dict
      (`InvalidAction` otherwise), then a recursive `_has_template(value: Any) -> bool` over dicts and lists raises
      `ActionNotAllowed(message(pack, "data_templates"))`, then the `_TARGET_KEYS` present in `data` go through the
      same id checks as `target`. A step without `action` keeps `action_step_service`. In `en.py` delete
      `action_not_allowed`, `data_variables_only`, `data_variables_mapping`, `data_variables_templates`; add
      `"data_templates": "Templates are only available to administrators"` and
      `"data_mapping": "{name} data must be a mapping"`.
- [ ] **Step 4:** `script/test tests/core tests/test_picked_shapes.py tests/test_websocket.py` — PASS. The existing
      `test_schedule_misshapen_picked_action_non_admin_invalid` may need its input changed to a still-invalid shape;
      keep its intent (non-admin gets `invalid`, not `unauthorized`).
- [ ] **Step 5:** `script/lint`, `script/type-check` green. Offer:
      `feat(service-actions): let any user schedule a single literal action`.

### Task 2: When a job is admin-only

**Files:**

- Modify: `custom_components/at/websocket_api.py:212-235` (`ws_schedule`), `:290-310` (`ws_reschedule`)
- Modify: `custom_components/at/core/manager.py:238-260` (`async_reschedule`)
- Test: `tests/test_websocket.py`, `tests/core/test_manager.py`

**Interfaces:**

- Produces: `JobManager.async_reschedule(job_id: str, due: datetime, source: Source | None = None, *,
raw_action: bool | None = None) -> Job` — `None` keeps the original's flag.

- [ ] **Step 1: Write the failing tests** in `tests/test_websocket.py`:
  - `test_schedule_single_action_admin_sets_raw_flag`: admin schedules
    `[{"action": "light.turn_on", "target": {"entity_id": "light.a"}}]` → stored job `raw_action is True`.
  - `test_schedule_any_single_action_non_admin_ok`: read-only user schedules
    `[{"action": "climate.set_temperature", "target": {"entity_id": "climate.a"}, "data": {"temperature": 21}}]` →
    success, `raw_action is False`.
  - `test_schedule_two_steps_non_admin_unauthorized`: two-step list → error code `unauthorized`.
  - `test_reschedule_by_admin_flags_copy`: non-admin's non-raw job, admin reschedules → copy `raw_action is True`,
    copy `source.user_id` is the admin's.
  - `test_reschedule_non_admin_keeps_flag`: non-admin reschedules a non-admin's job → copy `raw_action is False`.
  - In `tests/core/test_manager.py`: `async_reschedule(..., raw_action=True)` sets it; omitted keeps the original.

  Update `test_schedule_picked_action_non_admin_ok` and `test_run_now_picked_action` only if their fixtures relied
  on an admin scheduling a non-raw job.

- [ ] **Step 2:** `script/test tests/test_websocket.py tests/core/test_manager.py` — new tests FAIL.
- [ ] **Step 3: Implement.** In `ws_schedule`: `raw_action = connection.user.is_admin` after a passing
      `validate_picked_action` (the except branches stay). In `ws_reschedule`: pass
      `raw_action=job.raw_action or connection.user.is_admin`. In `async_reschedule`: use
      `original.raw_action if raw_action is None else raw_action`.
- [ ] **Step 4:** `script/test` — PASS. `script/lint`, `script/type-check` green. Offer:
      `feat(service-actions): treat jobs scheduled by an administrator as admin-only`.

### Task 3: The `at.schedule` action follows the same rule

**Files:**

- Modify: `custom_components/at/service_actions/schedule.py:66-80`
- Modify: `custom_components/at/translations/en.json:45`, `docs/user/CONFIGURATION.md:113`
- Test: `tests/test_services.py`

**Interfaces:**

- Consumes: `validate_picked_action` (Task 1); `async_require_admin(hass, context)` from `service_actions/common.py`.

- [ ] **Step 1: Write the failing tests** in `tests/test_services.py`:
  - `test_schedule_single_action_non_admin_ok`: `call(hass, "schedule", {"action": ACTION, "delay": {"minutes": 1}},
hass_read_only_user)` with `ACTION` a single literal step → job stored, `raw_action is False`.
  - `test_schedule_two_steps_non_admin_unauthorized`: two steps → `Unauthorized`.
  - `test_schedule_template_non_admin_unauthorized`: single step with a template in `data` → `Unauthorized`.
  - `test_schedule_misshapen_action_non_admin_invalid`: `data` a list → `ServiceValidationError`.
  - `test_schedule_single_action_admin_sets_raw_flag` → `raw_action is True`.
  - Keep `test_schedule_raw_action_from_automation_context_ok` (`raw_action is True`, no user).
    The existing `test_schedule_raw_action_non_admin_unauthorized` keeps passing only if its `ACTION` is multi-step or
    templated; change its input to a two-step list if not.
- [ ] **Step 2:** `script/test tests/test_services.py` — new tests FAIL.
- [ ] **Step 3: Implement.** Resolve the user from `call.context.user_id` (`hass.auth.async_get_user`). No user →
      `raw_action=True`, no check. Otherwise run `validate_picked_action`; on `ActionNotAllowed` →
      `await async_require_admin(...)` then `raw_action=True`; on `InvalidAction` → admin gets `raw_action=True`,
      non-admin gets a `ServiceValidationError` with the message (reuse the module's `_invalid` helper pattern with a
      new translation key `invalid_action` and placeholder `error`, added to `en.json` under `exceptions`); passing →
      `raw_action=user.is_admin`. Update the `action` field description in `en.json` to "An action to run later. Any
      user can schedule a single action; several steps or templates need an administrator." and the matching
      sentence in `CONFIGURATION.md:113`.
- [ ] **Step 4:** `script/test`, `script/hassfest`, `script/lint`, `script/type-check` green. Offer:
      `feat(service-actions): open at.schedule to any user for a single action`.

### Task 4: A deleted scheduler fails the job

**Files:**

- Modify: `custom_components/at/core/executor.py:33-38` (`_context`)
- Modify: `custom_components/at/lang/en.py` (failure reasons block near `:394`)
- Test: `tests/core/test_executor.py`

- [ ] **Step 1: Write the failing tests:**
  - `test_deleted_user_fails_job`: job with `source.user_id="gone"` (no such user) → `async_execute` raises
    `JobExecutionError` whose message is "The user who scheduled this job no longer exists"; the action's target
    service was not called.
  - `test_no_user_runs_without_user`: `source.user_id=None` → runs, the recorded service call's
    `context.user_id is None`.
  - Applies to intent jobs too: `test_deleted_user_fails_intent_job`.
- [ ] **Step 2:** `script/test tests/core/test_executor.py` — FAIL.
- [ ] **Step 3: Implement.** In `_context`, a set `user_id` that does not resolve raises
      `JobExecutionError(self._message("user_gone"))`; add `"user_gone": "The user who scheduled this job no longer
exists"` to `en.py`. Update the `_context` docstring.
- [ ] **Step 4:** `script/test` — PASS (check `tests/core/test_manager.py` and `tests/test_todo.py` for jobs built
      with a fake `user_id` that now fail; give them a real user or `None`). Lint and type-check green. Offer:
      `fix(executor): fail a job whose scheduling user no longer exists`.

### Task 5: Summaries name any action

**Files:**

- Modify: `custom_components/at/core/actions.py:171-186` (`summarize_action`), new `async_service_name`
- Modify: `custom_components/at/lang/__init__.py:49`, `custom_components/at/lang/en.py:317`
- Modify: callers — `custom_components/at/websocket_api.py` (`ws_schedule`),
  `custom_components/at/service_actions/schedule.py`
- Test: `tests/core/test_actions.py`

**Interfaces:**

- Produces: `async def async_service_name(hass: HomeAssistant, action: str) -> str | None` — the translated service
  name from `homeassistant.helpers.translation.async_get_translations(hass, hass.config.language, "services",
[domain])` key `component.{domain}.services.{service}.name`, else `None`.
- Produces: `summarize_action(hass, action, pack, service_name: str | None = None) -> str`.
- Produces: `LanguagePack.named_action_summary: str = "{action}: {name}"`.
- Produces: `async def async_summarize_action(hass: HomeAssistant, action: list[dict[str, Any]], pack: LanguagePack)
-> str` — looks up the service name for a single step and calls `summarize_action`; both callers use it.

- [ ] **Step 1: Write the failing tests:**
  - `summarize_action(hass, [{"action": "climate.set_temperature", "target": {"entity_id": "climate.living_room"}}],
EN, service_name="Set temperature")` == `"Set temperature: Living Room"` (state with friendly name
    "Living Room").
  - No target: `[{"action": "persistent_notification.create", "data": {...}}]`, `service_name="Create"` → `"Create"`.
  - Known verb wins: `light.turn_on` with `service_name="Turn on"` → `"Turn on Porch Light"` (today's phrase).
  - Two steps → `EN.generic_action_summary`.
  - `await async_service_name(hass, "light.turn_on")` returns a non-empty string after `light` is set up;
    `"nope.nothing"` → `None`.
- [ ] **Step 2:** `script/test tests/core/test_actions.py` — FAIL.
- [ ] **Step 3: Implement** as the interfaces say. `ws_schedule` and `async_handle_schedule` call
      `async_summarize_action` instead of `summarize_action`; a job's own `name` still wins in the service.
- [ ] **Step 4:** `script/test`, lint, type-check green. Offer:
      `feat(service-actions): name any scheduled action in its summary`.

### Task 6: Pick it with `ha-service-control`

**Files:**

- Modify: `frontend/src/ha-elements.ts` — add the on-demand loader
- Create: `frontend/src/components/pick-action.ts` — `at-pick-action`
- Create: `frontend/src/components/pick-fallback.ts` — today's verb/entity/variables controls moved out of the dialog
- Modify: `frontend/src/components/add-job-dialog.ts` — use `at-pick-action`, width
- Modify: `frontend/src/add-job.ts` — `fromServiceControl`
- Test: `frontend/test/ha-elements.test.ts`, `frontend/test/add-job.test.ts`, new `frontend/test/pick-action.test.ts`,
  `frontend/test/add-job-dialog.test.ts`

**Interfaces:**

- Produces (`ha-elements.ts`): `PICKER_ELEMENTS = ["ha-service-control", "ha-selector"]` (exact list from Task 0) and
  `loadPickerElements(timeoutMs = 10_000): Promise<string[]>` — memoized like `loadHaElements`, built on the
  existing `loadElements(registry, trigger, tags, timeoutMs)` with a trigger that loads the routes Task 0 found.
- Produces (`add-job.ts`): `fromServiceControl(value: { action?: string; target?: Record<string, unknown>; data?:
Record<string, unknown> } | undefined): Record<string, unknown>[] | undefined` — `undefined` when no action; omits
  empty `target` / `data`.
- Produces (both tab components): event `action-changed`, `detail: { action: Record<string, unknown>[] | undefined }`,
  `bubbles: false`. Properties: `hass`, and `ready: boolean` (the dialog sets it once per open from the loader result).

- [ ] **Step 1: Write the failing tests.**
  - `add-job.test.ts`: `fromServiceControl(undefined)` and `fromServiceControl({})` → `undefined`;
    `{action: "light.turn_on", target: {}, data: {}}` → `[{action: "light.turn_on"}]`;
    `{action: "light.turn_on", target: {entity_id: ["light.a"]}, data: {brightness_pct: 80}}` → one step with both.
  - `ha-elements.test.ts`: `loadPickerElements` reuses one promise across calls (pattern of the existing
    `loadHaElements` test).
  - `pick-action.test.ts` (happy-dom; register a stub `ha-service-control` element in the test):
    `ready=true` renders `ha-service-control`; a stub `value-changed` with `{value: {action: "light.turn_on", ...}}`
    fires `action-changed` with one step; a following `value-changed` with `{value: {}}` fires `action: undefined`;
    `ready=false` renders `at-pick-fallback`, whose selects produce `buildPickedAction` output.
  - `add-job-dialog.test.ts`: **Add** disabled until `action-changed` carries an action; a later
    `action: undefined` disables it again; submit sends `{action: [...], delay_seconds: 900}`. The loader resolving
    after the dialog is open does not swap the rendered tab during that open (Review Focus 4).
- [ ] **Step 2:** `npm --prefix frontend test` — FAIL.
- [ ] **Step 3: Implement.** Move the Pick it controls (`TOGGLE_DOMAINS`, `op`, `entity`, `varsText`) into
      `at-pick-fallback` unchanged in behaviour. `at-pick-action` renders `ha-service-control` with `.hass`, `narrow`
      and `.value`, mapping `value-changed` through `fromServiceControl`. The dialog calls `loadPickerElements()` on
      open, sets `ready = missing.length === 0` once, keeps `pickedAction` in state, and `canSubmit` for pick mode is
      `pickedAction !== undefined && whenValid`. Dialog width becomes `min(640px, calc(100vw - 32px))`.
- [ ] **Step 4:** If Task 0 found HA's popups need an `ha-dialog` parent, switch the dialog's shell (backdrop and
      `.dialog` div) to `ha-dialog` here, keeping the focus trap tests passing or replacing them with `ha-dialog`'s
      own behaviour; otherwise skip.
- [ ] **Step 5:** `npm --prefix frontend test`, `npm --prefix frontend run typecheck` — PASS.
      `script/build-frontend`. Offer: `feat(panel): pick any action with Home Assistant's action form`.

### Task 7: Sequence tab replaces Raw

**Files:**

- Create: `frontend/src/components/sequence-editor.ts` — `at-sequence-editor`
- Modify: `frontend/src/components/add-job-dialog.ts` — `Mode` becomes `"type" | "pick" | "sequence"`; tab label
  **Sequence**, admins only
- Test: new `frontend/test/sequence-editor.test.ts`, `frontend/test/add-job-dialog.test.ts`

**Interfaces:**

- Consumes: `loadPickerElements`, the `ready` property and `action-changed` event from Task 6; `parseRawAction`
  from `add-job.ts` for the fallback.

- [ ] **Step 1: Write the failing tests.**
  - `sequence-editor.test.ts` (stub `ha-selector`): `ready=true` renders `ha-selector` with
    `selector` deep-equal to `{ action: {} }`; `value-changed` with a two-step list fires `action-changed` with that
    list; an empty list fires `action: undefined`. `ready=false` renders the JSON textarea; valid JSON fires the
    parsed list, invalid JSON fires `undefined` and shows the existing inline error.
  - `add-job-dialog.test.ts`: the **Sequence** tab shows only when `isAdmin`; there is no **Raw** tab.
- [ ] **Step 2:** `npm --prefix frontend test` — FAIL.
- [ ] **Step 3: Implement.** Move the Raw textarea into the fallback branch of `at-sequence-editor`; the dialog drops
      `rawText`/`rawBad` and uses the shared `pickedAction`-style state for this tab (one `action` state per mode, so
      switching tabs does not carry an action across).
- [ ] **Step 4:** Frontend tests and typecheck PASS; `script/build-frontend`. Offer:
      `feat(panel): build multi-step jobs with Home Assistant's sequence editor`.

### Task 8: User docs and the live check

**Files:**

- Modify: `docs/user/CONFIGURATION.md:85-90`, `:164`

- [ ] **Step 1:** Rewrite the **Pick it** and **Raw** bullets: **Pick it** — choose any action, its targets and
      options, as in **Developer tools** > **Actions**; **Sequence** — administrators only, several steps with the
      automation editor's step list or YAML. Replace "Running a job that holds a raw action needs an administrator."
      with: a job scheduled by an administrator, or one with several steps or templates, can only be run now,
      rescheduled or completed by an administrator. Note that a job fails if the person who scheduled it has been
      removed. Same wording fix at `:164`.
- [ ] **Step 2:** `script/markdown` — 0 issues.
- [ ] **Step 3: Live check** with the `at-live-test` skill (restart the dev instance first — Python changed): as a
      non-admin via `script/ha`, schedule `climate.set_temperature` (or any non-toggle action on a demo entity) a few
      minutes out and confirm it is accepted with a "Set temperature: …" summary; as admin, schedule a two-step
      sequence; ask the developer to open the dialog and confirm both tabs render HA's elements. Cancel every job
      created. Report what was checked live versus by tests.
- [ ] **Step 4:** Full gate: `script/lint`, `script/type-check`, `script/hassfest`, `script/test`,
      `npm --prefix frontend test`, `npm --prefix frontend run typecheck`. Offer:
      `docs: describe any-action picking and the Sequence tab`.
