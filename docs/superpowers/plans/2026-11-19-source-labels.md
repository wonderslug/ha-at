# Source Labels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the panel's icon-based Source labels and the History cancellation text with plain `where · thing · person` labels that call every Assist path "Assist". This needs two newly recorded facts: the automation or script behind an `at.schedule` call, and the satellite behind a voice cancel.

**Architecture:** The backend records only ids, and every new field is additive (`Source.origin`, `Result.cancelled_device_id`, `Via.RESCHEDULE`). The panel resolves ids to names when it renders. One helper in `frontend/src/source.ts` serves both the Source column and the cancellation text.

**Tech Stack:** Python (Home Assistant custom integration, pytest), TypeScript + Lit (panel, vitest, vite).

**Spec:** [docs/superpowers/specs/2026-11-19-source-labels-design.md](../specs/2026-11-19-source-labels-design.md)

## Global Constraints

- Separator is `·` (space, U+00B7, space). No emoji or icons anywhere in either label.
- Unknown parts are omitted. Never print "User", "Unknown" or "Voice".
- Stored `via` values `voice`, `llm`, `panel`, `todo` and `service` keep their meaning. "Assist" exists only in panel text.
- New fields are additive: old stored jobs and old `at.list` readers keep working. There is no store version bump and no migration.
- Person name: the `person` entity whose `user_id` matches, else the signed-in user's own name when the ids match, else omitted. This is the existing `userName` in `source.ts`.
- Device name: `name_by_user ?? name` from `hass.devices`, omitted when the device is missing. Automation/script name: `friendly_name`, falling back to the entity id.
- Agent's call, stated in the handoff: when an automation or script is recorded and a user id is also known, the person is still appended (`Script · Bedtime · Brian`). This matches today's cancellation text.
- Validation uses project scripts only: `script/test`, `script/lint`, `script/type-check`, `npm --prefix frontend test`, `script/build-frontend`.
- Commit only when the developer asks. Each "Checkpoint" step offers the commit message and does not run it.

## Review Focus

1. **Jobs stored before this change** (no `origin`, no `cancelled_device_id`) must load, and must render as `Action · Brian` / `Cancelled from Assist by Brian`. The tests go in Task 1 (model) and Task 4 (frontend).
2. **A satellite or automation deleted after the job was made.** The device part disappears and the automation falls back to its entity id, with no crash and no "undefined". The tests go in Task 4.
3. **Another person's job.** The label shows their person name, not "User". If they have no person entity, the person part is omitted. The tests go in Task 4.
4. **An AI agent or MCP client (`via: llm`)** reads exactly like spoken Assist, and so does its cancellation. The tests go in Task 4.
5. **A script started by an automation** calling `at.schedule` records the script, which is the closer origin. `origin_entity_id` already does this. The test goes in Task 1.

---

### Task 1: Record the automation or script behind `at.schedule`

**Files:**

- Modify: `custom_components/at/core/models.py` (`Source`, `to_dict`, `from_dict`)
- Modify: `custom_components/at/core/actions.py` (`build_action_job`)
- Modify: `custom_components/at/voice/scheduling.py` (`async_schedule_command`)
- Modify: `custom_components/at/service_actions/schedule.py` (`async_handle_schedule`)
- Test: `tests/core/test_models.py`, `tests/test_services.py`

**Interfaces:**

- Produces: `Source.origin: str | None = None`, serialized as `source.origin` and read with `source.get("origin")`.
- Produces: the keyword argument `origin: str | None = None` on both `build_action_job(...)` and `async_schedule_command(...)`, which goes straight into `Source(origin=...)`.
- Consumes: `origin_entity_id(hass, context) -> str | None` from `core/context.py` (exists).

- [ ] **Step 1: Write the failing tests**

In `tests/core/test_models.py`, set `origin="automation.bedtime"` on `_action_job()`'s `Source`, so the existing `test_job_roundtrip` covers it. Then add:

```python
def test_old_source_without_origin_loads() -> None:
    data = _action_job().to_dict()
    del data["source"]["origin"]
    assert Job.from_dict(data).source.origin is None
```

In `tests/test_services.py`, add a test for each path:

```python
@pytest.mark.parametrize("data", [
    {"command": "turn on the porch light", "delay": {"minutes": 5}},
    {"action": ACTION, "delay": {"hours": 1}},
])
async def test_schedule_records_calling_automation(hass, manager, hass_admin_user, data) -> None:
    run = Context(user_id=hass_admin_user.id)
    hass.states.async_set("automation.bedtime", "on", context=run)
    response = await hass.services.async_call(DOMAIN, "schedule", data, blocking=True, return_response=True, context=run)
    assert manager.get(response["job_id"]).source.origin == "automation.bedtime"


async def test_schedule_from_script_called_by_automation_records_script(hass, manager) -> None:
    run = Context()
    hass.states.async_set("automation.bedtime", "on", context=run)
    hass.states.async_set("script.tidy_up", "on", context=run)
    response = await hass.services.async_call(
        DOMAIN, "schedule", {"command": "turn on the porch light", "delay": {"minutes": 5}},
        blocking=True, return_response=True, context=run,
    )
    assert manager.get(response["job_id"]).source.origin == "script.tidy_up"


async def test_schedule_without_automation_has_no_origin(hass, manager) -> None:
    response = await call(hass, "schedule", {"command": "turn on the porch light", "delay": {"minutes": 5}})
    assert manager.get(response["job_id"]).source.origin is None
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `script/test tests/core/test_models.py tests/test_services.py`
Expected: FAIL. `Source` has no `origin` (a `TypeError` in `_action_job`).

- [ ] **Step 3: Implement**

- Add `origin: str | None = None` as the last field of `Source`, then round-trip it in `to_dict` and `from_dict`.
- Add the `origin` keyword to `build_action_job` and `async_schedule_command`.
- In `async_handle_schedule`, compute `origin = origin_entity_id(hass, call.context)` once and pass it to both paths.

- [ ] **Step 4: Run them and confirm they pass**

Run: `script/test tests/core/test_models.py tests/test_services.py`
Expected: PASS

- [ ] **Step 5: Checkpoint.** Offer `feat(service-actions): record the automation or script that scheduled a job`.

---

### Task 2: Record the satellite behind a cancel

**Files:**

- Modify: `custom_components/at/core/models.py` (`Result`, `to_dict`, `from_dict`)
- Modify: `custom_components/at/core/manager.py` (`async_cancel`, `async_cancel_many`)
- Modify: `custom_components/at/voice/intents.py` (`AtCancelHandler._async_run`, two call sites)
- Test: `tests/core/test_models.py`, `tests/core/test_manager.py`, `tests/voice/test_intents.py`

**Interfaces:**

- Produces: `Result.cancelled_device_id: str | None = None`, serialized as `result.cancelled_device_id`.
- Produces: `JobManager.async_cancel(job_id, by, context=None, device_id: str | None = None)` and `async_cancel_many(job_ids, by, context=None, device_id: str | None = None)`. They store `device_id` on every cancelled job.

- [ ] **Step 1: Write the failing tests**

- `tests/core/test_models.py`: set `cancelled_device_id="sat-1"` in `_action_job()`'s `Result`, and in `test_old_result_without_cancel_details_loads` add `assert result.cancelled_device_id is None`.
- `tests/core/test_manager.py`, in `test_cancel_records_who_and_where`: pass `device_id="sat-1"` to the `async_cancel` call, then assert `first.result.cancelled_device_id == "sat-1"` and `other.result.cancelled_device_id is None`.
- `tests/voice/test_intents.py`:

```python
async def test_at_cancel_records_satellite(hass: HomeAssistant, manager: JobManager) -> None:
    await add_job(manager, "Turn on Porch Light", 1)
    await intent.async_handle(
        hass, "test", INTENT_CANCEL, {"all": {"value": True}}, language="en", device_id="sat-1"
    )
    assert manager.history()[0].result.cancelled_device_id == "sat-1"
```

Add the same assertion for the single-match path: cancel by `name`, and check `cancelled_device_id == "sat-1"`.

- [ ] **Step 2: Run them and confirm they fail**

Run: `script/test tests/core tests/voice/test_intents.py`
Expected: FAIL. `Result` has no `cancelled_device_id`.

- [ ] **Step 3: Implement.** Add the field and its round-trip, plus the manager keyword. In `AtCancelHandler._async_run`, pass `device_id=intent_obj.device_id` at both cancel calls. The LLM tools share this handler, so they get it for free.

- [ ] **Step 4: Run them and confirm they pass**

Run: `script/test tests/core tests/voice/test_intents.py`
Expected: PASS

- [ ] **Step 5: Checkpoint.** Offer `feat(voice): record which satellite cancelled a job`.

---

### Task 3: Tell a reschedule apart from Add job

**Files:**

- Modify: `custom_components/at/core/models.py` (`Via`)
- Modify: `custom_components/at/websocket_api.py` (`ws_reschedule`)
- Test: `tests/test_websocket.py` (`test_reschedule_copy`)

**Interfaces:**

- Produces: `Via.RESCHEDULE = "reschedule"`, the `source.via` of a copy made by `at/reschedule`.

- [ ] **Step 1: Change the test.** In `test_reschedule_copy`, assert `copy["source"]["via"] == "reschedule"` in place of `str(Via.PANEL)`.
- [ ] **Step 2: Run it.** Run `script/test tests/test_websocket.py -k reschedule`. Expected: FAIL, because `'panel' != 'reschedule'`.
- [ ] **Step 3: Implement.** Add the enum member, and have `ws_reschedule` build `Source(via=Via.RESCHEDULE, user_id=connection.user.id)`.
- [ ] **Step 4: Run it.** Run `script/test tests/test_websocket.py tests/voice`. Expected: PASS. The `tests/voice` run confirms "cancel all" still only skips `service` jobs.
- [ ] **Step 5: Checkpoint.** Offer `feat(panel): mark jobs created by rescheduling`.

---

### Task 4: Plain-text labels in the panel

**Files:**

- Modify: `frontend/src/types.ts` (`Job.source.origin?`, `Job.result.cancelled_device_id?`, both `string | null`, optional)
- Modify: `frontend/src/source.ts` (`sourceLabel`, `cancelDetail`; remove the icons and `CANCEL_WHERE`)
- Test: `frontend/test/source.test.ts`

**Interfaces:**

- Consumes: the `source.origin`, `result.cancelled_device_id` and `via: "reschedule"` values produced by Tasks 1 to 3.
- Produces (unchanged signatures): `sourceLabel(job, hass): string` and `historyDetail(job, hass): string`.
- New module-private helpers: `deviceName(id, hass): string | undefined`, `originName(entityId, hass): string` and the existing `userName`.

- [ ] **Step 1: Write the failing tests.** Extend the test fixture `hass` with `devices: { "sat-1": { name: "Satellite1", name_by_user: "Kitchen satellite" }, "phone": { name: "Brian's phone", name_by_user: null } }`. Let `job()` take a partial `source`. Replace the `"names where and who for each channel"` expectations and add a `sourceLabel` block. Every string below is exact:

```ts
describe("sourceLabel", () => {
  const src = (s: Partial<Job["source"]>) => sourceLabel(job("pending", {}, s), hass);
  it("calls every Assist path Assist", () => {
    expect(src({ via: "voice", device_id: "sat-1" })).toBe("Assist · Kitchen satellite");
    expect(src({ via: "voice", device_id: "sat-1", user_id: "u-brian" })).toBe("Assist · Kitchen satellite · Brian");
    expect(src({ via: "voice", user_id: "u-brian" })).toBe("Assist · Brian");
    expect(src({ via: "voice", device_id: "phone", user_id: "u-brian" })).toBe("Assist · Brian's phone · Brian");
    expect(src({ via: "llm", user_id: "u-brian" })).toBe("Assist · Brian");
    expect(src({ via: "voice" })).toBe("Assist");
  });
  it("names the panel action and the to-do list", () => {
    expect(src({ via: "panel", user_id: "u-brian" })).toBe("Add job · Brian");
    expect(src({ via: "reschedule", user_id: "u-brian" })).toBe("Reschedule · Brian");
    expect(src({ via: "todo", user_id: "u-brian" })).toBe("To-do list · Brian");
  });
  it("names the automation or script behind an action", () => {
    expect(src({ via: "service", origin: "automation.bedtime" })).toBe("Automation · Bedtime");
    expect(src({ via: "service", origin: "script.tidy_up", user_id: "u-brian" })).toBe("Script · Tidy up · Brian");
    expect(src({ via: "service", origin: "automation.gone" })).toBe("Automation · automation.gone");
    expect(src({ via: "service", user_id: "u-brian" })).toBe("Action · Brian");
    expect(src({ via: "service" })).toBe("Action");
  });
  it("leaves out what it cannot resolve", () => {
    expect(src({ via: "voice", device_id: "deleted" })).toBe("Assist");
    expect(src({ via: "panel", user_id: "stranger" })).toBe("Add job");
    expect(src({ via: "panel", user_id: "me" })).toBe("Add job · Me");
  });
});
```

New cancellation expectations, which replace the old channel lines:

```ts
expect(cancelled("panel", "u-brian")).toBe("Cancelled in the panel by Brian");
expect(cancelled("voice", "u-brian")).toBe("Cancelled from Assist by Brian");
expect(cancelled("llm", "u-brian")).toBe("Cancelled from Assist by Brian");
expect(cancelled("todo", "u-brian")).toBe("Cancelled from the to-do list by Brian");
expect(cancelled("service", null)).toBe("Cancelled by an action");
expect(
  historyDetail(
    job("cancelled", { cancelled_by: "voice", cancelled_user_id: "u-brian", cancelled_device_id: "sat-1" }),
    hass
  )
).toBe("Cancelled from Assist · Kitchen satellite by Brian");
expect(historyDetail(job("cancelled", { cancelled_by: "voice", cancelled_device_id: "deleted" }), hass)).toBe(
  "Cancelled from Assist"
);
```

The existing automation and script cancellation tests stay as they are ("Cancelled by automation Bedtime", "Cancelled by script Tidy up by Brian").

- [ ] **Step 2: Run them.** Run `npm --prefix frontend test`. Expected: FAIL on the new strings.
- [ ] **Step 3: Implement.** Write a module-private `where(via, origin, hass): string[]` that returns the first two parts:
  - `voice`/`llm` → `["Assist"]`
  - `panel` → `["Add job"]`
  - `reschedule` → `["Reschedule"]`
  - `todo` → `["To-do list"]`
  - `service` with an origin → `[capitalised domain, originName]`
  - `service` without one → `["Action"]`

  `sourceLabel` adds the device (Assist only) and the person, drops empty parts, and joins them with `·`. `cancelDetail` reuses `where` for the place phrase ("from Assist[ · device]", "in the panel", "from the to-do list", "by automation X", "by an action") and then appends `by <person>`.

- [ ] **Step 4: Run them.** Run `npm --prefix frontend test`. Expected: PASS.
- [ ] **Step 5: Checkpoint.** Offer `feat(panel): show where and who as plain text, with Assist for every voice path`.

---

### Task 5: Gates and bundle

- [ ] **Step 1:** Run `script/build-frontend`. Expected: exit 0, and `custom_components/at/frontend/at-panel.js` is rebuilt with no `🎙`, `🖱` or `⚙` in it (`rg -c "🎙|🖱|⚙" custom_components/at/frontend/at-panel.js` prints nothing).
- [ ] **Step 2:** Run `script/lint` and `script/type-check` until both exit 0.
- [ ] **Step 3:** Run `script/test`. Expected: the whole suite passes.
- [ ] **Step 4: Checkpoint.** Offer one squash title for the branch: `feat(panel): plain-text source labels that name Assist, the satellite and the automation`.
