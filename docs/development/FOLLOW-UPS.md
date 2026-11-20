# Follow-ups after v1

These are known minor issues that were reviewed and deferred while building v1. Each was triaged as safe to ship; fix them when convenient.

## Done

- AtCancel with a relative time ("the job in 20 minutes") raised `TimeParseError`; it now matches a job near now plus the offset (#4)
- Saving options reloaded the entry and interrupted running jobs; options now apply in place, and `defer_relative_to_ha` no longer needs a reload (#5)
- Task 2: redundant single-instance guard in the config flow removed (#6)
- Task 18: `on_stop` callback exceptions are now guarded in `async_stop` (#7)
- CUSTOMIZATION.md named this repository, not `jpawlowski/ha-integration-blueprint`, as the upstream (#8)
- Task 23: unused BuyMeCoffee/Discord badge comment removed from the README (#9)
- Task 11 "1 jobs" singular and Task 17 authorize-first ordering were already fixed and covered by tests (#10)
- Task 14: hassfest runs in the dev container and in CI, and passes
- Task 4: dead "forty five" number word removed, split patterns compiled once per language pack, `responses` typed as a mapping
- Task 5: `prune_history` docstring says a history job without `finished_at` is dropped
- Task 17: `async_require_admin` docstring covers a missing context
- Task 20: other users' jobs showed "User"; the panel now resolves every user's person name (#17)
- Task 1: blueprint_update tests pass and mise provides shellcheck and shfmt, so `script/shell-check` runs without `SKIP` in the dev container and CI; the macOS `git grep` behaviour was not re-checked on a Mac host
- Task 4: the `is_midnight` special case is gone with the unused `ResolvedTime.rolled_over` flag it fed; the spoken "tomorrow" comes from `day_qualifier()`
- Task 4: compound number words ("forty five", "one hundred and twenty") and clock times in words ("at seven thirty", "at seven oh five") parse everywhere, voice sentences included
- Task 5: one unreadable stored job no longer stops the integration loading; it is logged and kept aside under `unreadable` in the store, and the migrate function is tested
- Task 6: a job that finished while Home Assistant was stopping is stored as done, not interrupted; the grace window docs say it applies after a restart or reload
- Task 6: while a new or moved job is still being saved, run now is refused instead of silently doing nothing, and a cancel there no longer sends a scheduled event or arms a timer
- Task 7: picked actions aimed at an area, floor, device or label get a real summary ("Turn on Kitchen lights") instead of "Run action"; an invalid stored action's error names the action; the `script.turn_on` / `automation.trigger` limitation was already in Known limitations and the deleted-user context in the `_context` docstring
- Task 8: the logbook picks its language each time an entry is shown, and a test checks the real logbook loads the platform; the absolute import in `events.py` is what the import rules now require
- Task 10 and 11: a summary starting with an acronym ("TV off") keeps its capitals when spoken, through one `spoken_summary` helper shared by scheduling and queries; a job due yesterday or earlier says "yesterday" or its date instead of no day at all
- Task 11: jobs sharing a time are told apart by summary when cancelling ("cancel the turn off Porch Light job"), and "tonight" asked before 6 AM ends at 6 AM that morning

## Deferred minors

- Task 13: minor (deferred): "set the light brightness at 20" schedules at 8 PM (ambiguous digits).
- Task 13: minor (deferred): broadcast test patches intent.async_handle globally (brittle)
- Task 13: minor (deferred): no cancellation regression test for hand-off
- Task 14: minor (deferred): at.list exposes raw action bodies to non-admins; cancel/clear_history have no admin gate (spec: shared household queue, so OK)
- Task 14: minor (deferred): run_now error order for non-admin
- Task 16: minor (deferred): unique_id/EntityDescription convention & duplicated sensor boilerplate; \_unrecorded_attributes for jobs/summary; no unload test
- Task 17: minor (deferred): history->needs_action silently ignored; tests poke manager.\_jobs
- Task 19: minor (deferred): no CI bundle-freshness check; npm audit dev-only picomatch
- Task 19: minor (deferred): script/build-frontend not shellcheck-verified; spell scripts now excluded from template sync (document)
- Task 20: minor (deferred): no DOM tests for components; row cancel has no confirm
- Task 20: minor (deferred): wallTimeToDate gap time resolves 1h EARLIER (backend moves forward) — align in final review
- Task 21: minor (deferred): single-entity picker; no focus trap; no component tests for debounce
- Task 21: minor (deferred): Escape during in-flight submit resets busy dialog
- Source labels (#17): minor (deferred): no backend test that an LLM cancel records `llm_context.device_id` as `cancelled_device_id` (same code path as voice, which is tested)
- Source labels (#17): minor (deferred): no frontend test for an Assist cancel with a device but no person ("Cancelled from Assist · Kitchen satellite"), or for an `llm` cancel with a device
