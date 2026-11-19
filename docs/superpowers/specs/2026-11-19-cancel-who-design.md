# History details: who and where — design

A small change, approved by the author on 2026-11-19. It follows the
[panel list layout](2026-11-19-panel-list-layout-design.md).

## Intent

The History card's last column held only a failure's error, so most rows were blank. The author wants each finished
job to explain itself the way Activity (the logbook) does, giving **where** an action came from and **who** did it.

## Decisions

- Rename the column **Details**, with this content per status:
  - **Failed:** the error, as before.
  - **Missed:** "Home Assistant was off when it was due". That is the only way a job is missed.
  - **Cancelled:** where and who, for example "Cancelled from the panel by Brian", "Cancelled with voice by Brian",
    "Cancelled by automation Bedtime" or "Cancelled by an action by Brian".
  - **Done:** empty.
- "Who" comes from the Home Assistant `Context` of the cancelling call, which is what Activity uses:
  - `Result` gains `cancelled_user_id` and `cancelled_origin`. The origin is the entity id of the automation or
    script whose current run context matches the call's context.
  - The panel resolves the user id to a name through `person` entities, falling back to the current user.
  - It resolves the origin to the entity's friendly name.
- Cancel paths pass their context: the WebSocket command uses `connection.context(msg)`, the action uses
  `call.context`, voice uses `intent_obj.context`, and the to-do list uses the entity's `_context`.
- Job events are fired with the context of the call that caused them, so Activity shows the same who and where.
- **Scope:** "who" is recorded for cancellations only (agent's call; recording it for scheduling is a separate change).
- **Compatibility:** stored jobs only gain fields. Old jobs load as before and show only the channel. This is not a
  breaking change.

## Approaches

| Approach                                                               | Trade-off                                                                                                                                                                     |
| ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Channel only (`cancelled_by`), frontend-only                           | No backend change, but no "who". **Rejected by the author.**                                                                                                                  |
| **Record the context at cancel time and resolve the origin in memory** | **Picked.** Matches Activity's who and where without a recorder query. The origin is lost if the automation runs again before the match, which cannot happen within one call. |
| Query the logbook from the panel for each job                          | Exactly Activity's text, but one query per row, and logbook queries cannot filter by our event types.                                                                         |

## Plan

1. `core/models.py`: add `Result.cancelled_user_id` and `cancelled_origin`, and round-trip them. Test:
   `test_job_roundtrip` with both set, and old data without them loading as `None`.
2. `core/context.py`: `origin_entity_id(hass, context) -> str | None` finds the `automation.*` or `script.*` state
   whose `context.id` equals `context.id`. Tests cover the match, no match, and `None` context.
3. `core/manager.py`: `async_cancel` and `async_cancel_many` take `context: Context | None = None`, store the user
   id and origin, and fire the cancelled event with that context. `core/events.py`: `fire_job_event(..., context=None)`.
   Tests: the user id and origin are stored, and the event's `context.id` matches.
4. Call sites: the WebSocket command, action, voice and to-do paths pass their context. Each existing cancel test
   asserts `cancelled_user_id`.
5. Frontend: `cancelDetail` and `historyDetail(job, hass)` in `source.ts`, unit-tested for every status and channel,
   with and without user and origin. `Result` type gains the two fields. The History column becomes "Details".
6. Gates: `script/lint`, `script/type-check`, `script/test`, frontend tests, and `script/build-frontend`.
