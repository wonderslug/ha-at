# Add job dialog with Home Assistant's pickers — design

A project-sized change to the Scheduled Jobs panel's **Add job** dialog and to the rule that decides who may
schedule which action.

## Intent

**Pick it** today offers five fixed verbs (turn on, turn off, toggle, run script, trigger automation) and one flat
entity dropdown. The author wants any action a scheduled job can run to be set up from the dialog, with Home
Assistant's own pickers. Once an action is chosen, the target choices narrow to what that action accepts, and the
action's own options appear as proper fields. The author asked to **follow the Home Assistant pattern** for who may
do what, and to give admins HA's step-by-step sequence editor in place of the JSON **Raw** tab.

## Goals, non-goals, anti-goals

- Goal: any user can schedule any single action, with any target and options, through HA's own action form.
- Goal: admins can build multi-step jobs (several steps, delays, conditions) with HA's sequence editor.
- Goal: permissions match what Home Assistant itself allows a signed-in user.
- Non-goal: changes to **Type it** (the natural-language field), the **When** section, the job list, voice, or the
  LLM tools.
- Non-goal: editing an existing job's action. Jobs stay immutable once queued.
- Anti-goal: our own lookalike pickers that drift from HA's (the author rejected those for the panel list too; see
  [2026-11-19-panel-list-layout-design.md](2026-11-19-panel-list-layout-design.md)).
- Anti-goal: a non-admin gaining more power through a scheduled job than an immediate call from HA's own frontend
  would give them.

## Permissions: the Home Assistant pattern

Verified against the installed Home Assistant `components/websocket_api/commands.py`: `call_service` (one action,
with target and data) has no admin check and runs as the calling user, so HA's entity permissions apply.
`execute_script` (a whole sequence) is admin-only, as are `fire_event`, `subscribe_trigger` and `test_condition`.

The new rule, applied identically by the panel's websocket `at/schedule` command and the `at.schedule` action:

| The action                                                                   | Who may schedule it |
| ---------------------------------------------------------------------------- | ------------------- |
| Exactly one step of the form `{action, target?, data?}`, literal values only | Any user            |
| Anything else: several steps, `delay`, `if`, `choose`, `event`, templates, … | Admins only         |

Details of the single-step rule (replacing the allowlist in `validate_picked_action`,
[`core/actions.py`](../../../custom_components/at/core/actions.py)):

- `action` is any `domain.service` string. The verb and domain allowlist goes away.
- `target` is optional (some actions take none, such as `notify.*` or `persistent_notification.create`). When
  present, it keeps today's checks: only `entity_id`, `area_id`, `device_id`, `floor_id`, `label_id`, explicit ids.
- **"all" and "none" stay rejected as targets — author's call to confirm; proposed by the designer.** HA itself
  allows them, but a scheduled "everything off" is easy to set up by accident and hard to notice before it fires.
- `data` is any mapping, with **no templates anywhere in it, at any depth** (the designer's call). `call_service`
  never renders templates, but jobs run through HA's script engine, which does; allowing them would give a
  non-admin more than `call_service` does. The check walks nested dicts and lists.
- Target keys inside `data` (`entity_id`, `area_id`, `device_id`, `floor_id`, `label_id`) get the same checks as
  `target` (the designer's call); HA still accepts them there, so otherwise `data: {entity_id: "all"}` would get
  around the "all" rejection.
- Actions HA registers as admin-only (`homeassistant.restart`, the `reload` actions) are **not** refused at schedule
  time (the designer's call): HA keeps no public list of them. A non-admin's job for one fails when it fires, with
  HA's Unauthorized error in History. Nobody gains power.
- No other step keys (`continue_on_error`, `response_variable`, `enabled`, `alias`, …). A form step from
  `ha-service-control` produces only `action`, `target` and `data`.
- The job runs as the user who scheduled it — already true
  ([`core/executor.py`](../../../custom_components/at/core/executor.py) `_context`), so HA's permission checks apply
  when it fires, exactly as for an immediate call.

### Who may act on a job someone else scheduled (author's decision)

A job runs as the user who scheduled it, so a job that carries admin rights must not be triggerable by a non-admin.
The stored `raw_action` flag ("only an admin may run now, reschedule or complete this job") keeps its name and that
meaning, but it is now set when **any** of these holds:

- the action fails the single-step rule (several steps, templates, …), as today;
- the scheduling user is an admin;
- there is no scheduling user (`at.schedule` from an automation or script), as today.

Consequence the author accepted: other household members can no longer **Run now**, reschedule or complete an
admin's simple jobs. Jobs already stored keep their flag; no storage migration, no change to the job shape. Voice and
typed jobs (intent jobs) are unaffected; the flag only applies to action jobs.

### The `at.schedule` action

Gets the same rule as the panel (the designer's call, following from "the HA pattern"): a signed-in non-admin may
schedule one single-step action through it; anything else still needs an admin. Today it requires an admin for every
`action` and always stores `raw_action=True`; it now runs the single-step rule and sets the flag as above.

### A deleted scheduling user (author's decision)

Today, if the user who scheduled a job no longer exists when it fires, `_context` falls back to a context with no
user, which skips HA's permission checks. Instead, a job whose stored `user_id` no longer resolves to a user
**fails** with a new language-pack message ("The user who scheduled this job no longer exists"). Jobs with no stored
user (from automations) keep running with no user, as today. This changes the outcome for jobs already queued,
voice jobs included.

- Error messages for a rejected action come from the language pack, as today. Allowlist messages that can no longer
  occur (`action_not_allowed`, `data_variables_only`, `data_variables_mapping`, `data_variables_templates`) are
  removed; a new `data_templates` message ("Templates are only available to administrators") is added. English only;
  other languages fall back to English per the project's translation rule.

This widens what non-admins can do; it removes nothing anyone relies on, so it is not a breaking change.

### Summaries

`summarize_action` today names known verbs ("Turn on Porch Light") and falls back to a generic "Run action". With
any action allowed, the fallback gets more common. **Designer's call:** when the pack has no verb for the action,
use the action's own name from HA's service descriptions (the name `ha-service-control` shows, for example "Set
temperature"), followed by the target names: "Set temperature: Living Room". The generic phrase stays the last
resort. Multi-step admin jobs keep the generic phrase unless given a name.

## Approaches

| Approach                                                                            | Trade-off                                                                                                                   |
| ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **A. Use HA's ready-made elements: `ha-service-control` and the `action` selector** | **Picked.** Least code; looks and behaves exactly like HA. Depends on more HA frontend internals to get them loaded.        |
| B. Assemble Pick it from `ha-service-picker`, the target selector and `ha-form`     | More control over layout and filtering, but rewrites logic HA already maintains and needs the same loading trick. Fallback. |
| C. Our own fields generated from `hass.services` descriptions                       | No internals, but much more work and worse: no colour pickers, sliders, or area and device targeting. Rejected.             |

B is the documented fallback for **Pick it** only, if the spike shows `ha-service-control` misbehaves outside its
own page.

## The dialog

```text
┌ Add job ─────────────────────────────────────┐
│  Type it   Pick it   Sequence (admins only)  │
│                                              │
│  Pick it:   <ha-service-control>             │
│             Action  [ Light: Turn on      ▾] │
│             Targets [ + Area  + Device ... ] │
│             Brightness ──●──────  80 %       │
│             Color      [ ● ]                 │
│                                              │
│  Sequence:  <ha-selector selector={action}>  │
│             (HA's step list + YAML view)     │
│                                              │
│  When       (+15m) (+1h) [ date & time ]     │
│                                 Cancel  Add  │
└──────────────────────────────────────────────┘
```

- **Pick it** is `ha-service-control`, given `hass` and `narrow`, listening for `value-changed`. Its value
  (`{action, target, data}`) is sent as a one-step action list. **Add** is enabled once an action is chosen and the
  **When** section is valid; the server's validation is the authority on the rest.
- **Sequence** replaces **Raw**, shown only to admins as **Raw** is today. It is an `ha-selector` with
  `selector: {action: {}}`, which renders the automation editor's step list and has a YAML view for pasting.
  **Add** is enabled when the list has at least one step.
- The dialog widens (to about 640 px) for these tabs, since HA's forms are designed for wider space; it stays
  full-width on phones.
- Non-admins who build something the rule forbids (a template typed into a field, for example) get the server's
  message in the existing error banner.
- The `TOGGLE_DOMAINS` list, the verb select, the script-variables textarea and `buildPickedAction` go away when the
  HA elements load.

### Loading the elements

Both elements are code-split. In the installed frontend (20260930.5), `ha-service-control` and `ha-service-picker`
are in one chunk, the target picker in another, and `ha-selector-action` in a third; they register only when a
page that uses them opens. The existing loader ([`ha-elements.ts`](../../../frontend/src/ha-elements.ts)) already
opens HA's config panel and its automation page behind the scenes. It is extended to also load the route(s) that
register these elements — Developer Tools' action page for `ha-service-control`, the automation editor for the
`action` selector. The spike decides the exact routes.

Unlike the panel list, these elements load **lazily, when the dialog first opens**, not at panel start, so a failure
here never blocks the job list.

### Fallback

The panel-list design chose no fallback. Approach A, as picked, keeps one here: if an element is
not defined after the loader's timeout, that tab falls back to today's controls — the plain verb and entity
dropdowns for **Pick it**, the JSON textarea for **Sequence** — and logs the missing tags, as the list loader does.
The fallback controls keep producing shapes the new rule accepts.

## Spike first

Before the plan's real work, a throwaway spike (no tests, not merged) answers, against the dev instance:

1. Which route loads register `ha-service-control` and `ha-selector-action` from inside the custom panel.
2. Whether `ha-service-control` renders, filters targets by the chosen action, and emits a usable value inside our
   dialog's shadow root (HA's own pickers open popups that may assume an `ha-dialog` parent).
3. Whether the action selector's step editor works there, including its add-step menu and YAML view.
4. Whether either element needs extra setup (`hass.services` descriptions loaded, `ha-dialog` instead of our own
   dialog shell).

If 2 fails, Pick it moves to approach B. If the popups need `ha-dialog`, the dialog shell switches to `ha-dialog`
(already in the bundle) as part of this work. Findings go in
[`SPIKE-FINDINGS.md`](../../development/SPIKE-FINDINGS.md), closing the pending Task 21 check there.

## Tests

- Backend: `tests/core/test_actions.py` and `tests/test_picked_shapes.py` cover the new single-step rule (any
  action, optional target, nested data, nested templates rejected, extra step keys rejected, "all" rejected);
  `tests/test_services.py` and the websocket tests cover a non-admin scheduling `climate.set_temperature` and
  being refused a two-step list; summaries cover the service-name fallback; an admin's single action is stored
  with `raw_action=True` and a non-admin cannot run it now, reschedule it or complete it (panel, `at.run_now`, to-do);
  the executor fails a job whose scheduling user was deleted and still runs one with no stored user.
- Frontend: the dialog tests replace the HA elements with stub custom elements that fire `value-changed`, and cover
  the fallback path when they are undefined. `picked-shapes.json` gains cases for the new shapes.
- Live check on the dev instance with `at-live-test`: one non-admin single action, one admin sequence, both
  cancelled afterwards.

## Left to the builder

- File layout in the frontend (one component per tab is fine).
- How the summary looks up the service name (HA's `async_get_all_descriptions` or the translations cache).
- Exact dialog width and responsive breakpoint.
- Whether the fallback **Pick it** keeps its current verbs only or is widened; it only needs to keep working.
