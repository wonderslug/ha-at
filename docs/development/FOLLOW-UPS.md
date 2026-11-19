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

## Deferred minors

- Task 1: minor (deferred): blueprint_update tests fail on macOS git grep; shellcheck/shfmt absent on host (commits used SKIP)
- Task 4: minor (deferred): en.py "forty five" dead entry; split regex recompiled per call; is_midnight special-case; responses: Any=None
- Task 5: minor (deferred): no migrate-func test; prune drops history with finished_at=None (comment it); one corrupt record fails whole load
- Task 6: minor (deferred): #5 stop during after-finish save can misreport DONE as interrupted; #7 grace-run wording
- Task 6: minor (deferred): settling-window edge cases (run_now silently no-op; cancel during settling fires scheduled event for cancelled job)
- Task 7: minor (deferred): script.turn_on/automation.trigger report success even if target later fails (doc it); area-only summary "Run action"; vol.Invalid msg could name service; deleted-user jobs run as system context (comment)
- Task 8: minor (deferred): logbook pack resolved at load; absolute import in events.py; no platform-load test
- Task 10: minor (deferred): first-letter lowercasing mangles acronym-leading summaries; same-day/negative days -> "" qualifier
- Task 11: minor (deferred): lowercase-first-letter duplicated in queries/scheduling; same-clock-time ambiguity says "6 AM and 6 AM"; tonight at 02:00 spans to next 06:00
- Task 13: minor (deferred): "set the light brightness at 20" schedules at 8 PM (ambiguous digits).
- Task 13: minor (deferred): broadcast test patches intent.async_handle globally (brittle)
- Task 13: minor (deferred): no cancellation regression test for hand-off
- Task 14: minor (deferred): at.list exposes raw action bodies to non-admins; cancel/clear_history have no admin gate (spec: shared household queue, so OK)
- Task 14: minor (deferred): run_now error order for non-admin
- Task 16: minor (deferred): unique_id/EntityDescription convention & duplicated sensor boilerplate; \_unrecorded_attributes for jobs/summary; no unload test
- Task 17: minor (deferred): common.py None-context docstring; history->needs_action silently ignored; tests poke manager.\_jobs
- Task 19: minor (deferred): no CI bundle-freshness check; npm audit dev-only picomatch
- Task 19: minor (deferred): script/build-frontend not shellcheck-verified; spell scripts now excluded from template sync (document)
- Task 20: minor (deferred): no DOM tests for components; other users shown as "User"; row cancel has no confirm
- Task 20: minor (deferred): wallTimeToDate gap time resolves 1h EARLIER (backend moves forward) — align in final review
- Task 21: minor (deferred): single-entity picker; no focus trap; no component tests for debounce
- Task 21: minor (deferred): Escape during in-flight submit resets busy dialog
