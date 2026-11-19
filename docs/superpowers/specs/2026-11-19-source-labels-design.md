# Source labels: where and who, without icons — design

A small change, approved by the author on 2026-11-19. It follows
[History details: who and where](2026-11-19-cancel-who-design.md).

## Intent

The panel's Source column mixed emoji icons with channel names. It said "Voice" for anything that came through Assist,
"User" for anyone but the viewer, and "Automation" for every `at.schedule` call. The author wants plain-text labels
that name Assist generically, whether the request was spoken, typed or came from an agent. Each label should add the
specific place (satellite, automation, panel dialog) and the person whenever those are known.

## Decisions

- **Shape:** `where · specific thing · person`, joined with `·`, with no icons. Any part that isn't known is left
  out. Labels never say "User", "Unknown" or "Voice".
- **Source column (Upcoming and History):**

  | Came from                                                   | Shows                                               |
  | ----------------------------------------------------------- | --------------------------------------------------- |
  | Spoken to a satellite                                       | `Assist · Kitchen satellite` (`· Brian` when known) |
  | Typed into Assist in the browser                            | `Assist · Brian`                                    |
  | Typed into Assist in the phone app, with the phone a device | `Assist · Brian's phone · Brian`                    |
  | AI agent behind Assist, or an MCP client (`via: llm`)       | `Assist · Brian`                                    |
  | Add job dialog                                              | `Add job · Brian`                                   |
  | Rescheduling a finished job from History                    | `Reschedule · Brian`                                |
  | Scheduled Jobs to-do list                                   | `To-do list · Brian`                                |
  | `at.schedule` from an automation / a script                 | `Automation · Morning lights` / `Script · Bedtime`  |
  | `at.schedule` from anywhere else                            | `Action · Brian`, or `Action`                       |

- **Cancellations (History Details):** use the same vocabulary. Examples: "Cancelled from Assist · Kitchen satellite
  by Brian", "Cancelled in the panel by Brian", "Cancelled from the to-do list by Brian", "Cancelled by automation
  Morning lights", "Cancelled by an action".
- **Person:** resolved from the `person` entity with that `user_id`, falling back to the signed-in user's own name. This
  is the existing `userName` helper, now used by both columns.
- **Device:** `name_by_user`, falling back to `name`. **Automation/script:** its friendly name, falling back to the
  entity id.
- Names are resolved when the panel renders, so renames update old rows. If a device or automation is deleted, that
  part drops out of older rows.
- Stored `via` values (`voice`, `llm`, …) do not change. "Assist" exists only in the panel's wording.
- **"Reschedule"** is the agent's label for the History action. The author may rename it.

## Approaches

| Approach                                                                    | Trade-off                                                                                                                    |
| --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **A. Add `source.origin` and `result.cancelled_device_id`; panel words it** | **Picked.** Smallest change, and `at.list` output only gains fields. A deleted device or automation drops out of old labels. |
| B. Replace the `cancelled_*` fields with a `cancelled_source: Source`       | Created and cancelled are recorded the same way, but it breaks `at.list` readers and needs a store migration.                |
| C. Build the label text in the backend                                      | `at.list` and voice could reuse it, but stored text goes stale and the panel's wording moves to Python.                      |

## Plan

1. `core/models.py`: add `Source.origin: str | None` and `Result.cancelled_device_id: str | None`, and round-trip
   both. Old data loads with `None`. Test: the round-trip with both fields set, and old data without them.
2. Creation: the `at.schedule` handler records `origin_entity_id(hass, call.context)`. `build_action_job` and
   `async_schedule_command` take `origin`. Test: a call from an automation's context stores its entity id.
3. Cancellation: `async_cancel` / `async_cancel_many` take `device_id: str | None = None` and store it. The voice
   cancel intents pass `intent_obj.device_id`. Test: a voice cancel with a device stores it.
4. Reschedule: tell it apart from Add job. Either add a `Via.RESCHEDULE`, or mark the copy (builder's call; the
   label is all that matters).
5. Frontend `source.ts`: one `originParts(...)` builds the `where · thing · person` parts. `sourceLabel` and
   `cancelDetail` both use it. Remove the icons. Update the `Source`/`Result` types. Unit-test every row of both
   tables, with and without the person, the device and the origin.
6. Gates: `script/lint`, `script/type-check`, `script/test`, frontend tests, and `script/build-frontend`.

## Compatibility

Stored jobs and `at.list` output only gain fields. Jobs that already exist from automations show `Action`, because
their origin was never recorded. This is not a breaking change.
