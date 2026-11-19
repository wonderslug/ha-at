# Panel list layout — design

A small change to the Scheduled Jobs sidebar panel (spec 2026-11-17, §7.5).

## Intent

Make the panel look and behave like a standard Home Assistant list page, such as Labels or Dashboards. The
author asked for three things: **Add job** at the bottom, like "+ Add integration"; **Upcoming** and
**History** in the page body instead of as header tabs; and Home Assistant's own themes and components
rather than lookalikes, even at the cost of coupling to its frontend internals.

## Goals, non-goals, anti-goals

- Goal: the panel is built from Home Assistant's own frontend elements, so theme, typography, spacing,
  dark mode and future redesigns come from Home Assistant itself.
- Non-goals: search, column pickers and multi-select. Changes to the backend or the WebSocket API. Using
  HA pickers in the add-job dialog (a separate follow-up, agreed).
- Anti-goal: our own styled imitation of HA components that drifts from the real ones.

## Approaches

| Approach                                                        | Trade-off                                                                                               |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 1. Own Lit components styled with HA theme variables            | Stable, but an imitation. **Rejected by the author:** it drifts from HA's look.                         |
| **2. Load HA's lazily loaded elements at startup and use them** | **Picked.** Native look and feel. Couples to HA frontend internals; a renamed element breaks the panel. |
| 3. HA elements when present, own components otherwise           | Two code paths for every part. **Rejected:** the fallback is the drift the author wants to avoid.       |

## Loading HA's elements

The list-page elements are code-split and only load when a page using them opens. At startup the panel
triggers the load of HA's config panel through `partial-panel-resolver`'s route table (the technique other
custom panels use), then awaits `customElements.whenDefined()` for every element below, with a timeout.

If any element is missing, the panel shows only a plain message: this panel needs an update for this Home
Assistant version, naming the missing elements, and logs the same to the console. There is no fallback
look (author's decision). Jobs keep running and remain reachable through voice, the to-do list and actions.

Elements used, verified against HA 2026.10.4:

| Element                    | Used for                                                                |
| -------------------------- | ----------------------------------------------------------------------- |
| `hass-subpage` (main-page) | App bar, title, sidebar ☰ on narrow screens, the `fab` slot            |
| `ha-card`                  | The Upcoming and History sections                                       |
| `ha-data-table`            | The rows in both cards                                                  |
| `ha-button` `size="l"`     | "+ Add job" in the `fab` slot, as HA's own list pages do                |
| `ha-icon-button`           | Row actions: run now, cancel                                            |
| `ha-dropdown`              | The ⋮ menu in the app bar: Cancel all, Clear history                    |
| `ha-svg-icon`              | Icons, with paths from `@mdi/js` (new frontend dependency, tree-shaken) |
| `ha-filter-chip`           | History status filter                                                   |

## Layout (author's choice: two stacked sections)

```text
┌──────────────────────────────────────┐
│ ☰ Scheduled Jobs                  ⋮  │  hass-subpage app bar
├──────────────────────────────────────┤
│ ┌ Upcoming (3) ────────────────────┐ │  ha-card + ha-data-table
│ │ When    Job          Source  ▶ ✕ │ │
│ └──────────────────────────────────┘ │
│ ┌ History ───── All ✓ ✗ ⚠ ⊘ ───────┐ │  ha-card + filter chips + ha-data-table
│ │ ✓  2h ago  Fan on       Re-sched │ │
│ │ … (15 most recent)      Show all │ │
│ └──────────────────────────────────┘ │
│                         ( + Add job )│  ha-button in the fab slot
└──────────────────────────────────────┘
```

Columns, row clicks (open details) and row actions are unchanged from §7.5 of the 2026-11-17 design.

## Calls made by the agent (open to correction)

- **History cap:** the 15 most recent rows matching the filter, with "Show all (n)" to expand for the rest
  of the visit. The cap is a pure function in `state.ts` with a unit test.
- **The ⋮ menu stays in the app bar** with Cancel all and Clear history.
- **Cards are capped at about 1000px and centred** on wide screens, like HA's own list pages.
- **The add-job and details dialogs** keep their current look in this change. Moving them onto
  `ha-dialog` belongs with the picker follow-up.
- **Element check:** the loader and the missing-element message live in their own module with a unit
  test for the "something is missing" path.
- **Spec and bundle:** §7.5 of the 2026-11-17 design is updated, and `at-panel.js` is rebuilt with
  `script/build-frontend`.
- **Verification:** the panel is checked in the dev container's Home Assistant, since unit tests cannot
  load HA's real elements.

## Left to the builder

The exact `ha-data-table` column definitions, the loader's timeout, and how the card heading and the filter
chips share one row on narrow screens.
