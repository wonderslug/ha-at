# Follow-ups after v1

These are known minor issues that were reviewed and deferred while building v1. Each was triaged as safe to ship; fix them when convenient.

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
- Task 14: minor (deferred): hassfest never run on host (run in final gate/CI); run_now error order for non-admin
- Task 16: minor (deferred): unique_id/EntityDescription convention & duplicated sensor boilerplate; \_unrecorded_attributes for jobs/summary; no unload test
- Task 17: minor (deferred): common.py None-context docstring; history->needs_action silently ignored; tests poke manager.\_jobs
- Task 19: minor (deferred): no CI bundle-freshness check; npm audit dev-only picomatch
- Task 19: minor (deferred): script/build-frontend not shellcheck-verified; spell scripts now excluded from template sync (document)
- Task 20: minor (deferred): no DOM tests for components; other users shown as "User"; row cancel has no confirm
- Task 20: minor (deferred): wallTimeToDate gap time resolves 1h EARLIER (backend moves forward) — align in final review
- Task 21: minor (deferred): single-entity picker; no focus trap; no component tests for debounce
- Task 21: minor (deferred): Escape during in-flight submit resets busy dialog
