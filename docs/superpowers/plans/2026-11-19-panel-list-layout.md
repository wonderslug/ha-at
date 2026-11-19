# Panel list layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Scheduled Jobs panel from Home Assistant's own frontend elements, with Upcoming and History as
two stacked cards and "+ Add job" as the floating button.

**Architecture:** At startup the panel loads HA's config panel code through `partial-panel-resolver`, which registers
the lazily loaded list-page elements, then waits for each required tag. If any tag is missing it renders only a
"needs an update" message. Otherwise `at-panel` renders `hass-subpage` (main-page) with two `ha-card`s holding
`ha-data-table`s, a `ha-dropdown` overflow menu and a `ha-button size="l"` in the `fab` slot.

**Tech Stack:** TypeScript 5.9, Lit 3.3, Vite 8, Vitest 5 (node environment, no DOM), `@mdi/js` (new).

**Spec:** [`docs/superpowers/specs/2026-11-19-panel-list-layout-design.md`](../specs/2026-11-19-panel-list-layout-design.md)

## Global Constraints

- Use HA's elements, never a styled imitation; no fallback look when an element is missing (author's decision).
- Required elements, verified against HA 2026.10.4: `hass-subpage`, `ha-card`, `ha-data-table`, `ha-button`,
  `ha-icon-button`, `ha-dropdown`, `ha-dropdown-item`, `ha-svg-icon`, `ha-filter-chip`.
- No own colours, radii, shadows or fonts on HA elements; only layout CSS (max width ~1000px centred, gaps, padding).
- History shows the 15 most recent rows matching the filter, then "Show all (n)".
- Columns, row click (open details) and row actions are unchanged from §7.5 of the 2026-11-17 design.
- Add-job and details dialogs are out of scope; they keep their current look.
- No backend, WebSocket API or Python changes.
- Commit only when the developer asks (`AGENTS.md`); each task ends at a green state instead of a commit.
- Frontend tests: `npm --prefix frontend test`; types: `npm --prefix frontend run typecheck`; bundle:
  `script/build-frontend`.

## Review Focus

1. **HA loaded the elements slowly or partly** — the panel must show the "needs an update" message naming exactly the
   missing tags after the timeout, never a blank page. Test in Task 2.
2. **Loader called twice** (panel reconnected, re-attached) — the second call reuses the first promise and does not
   reload the config panel. Test in Task 2.
3. **History filter with fewer than 15 matches, or exactly 15** — no "Show all" link. Test in Task 1.
4. **Filter changed while expanded** — expansion stays, count reflects the new filter. Test in Task 1.
5. **Row button click also opening details** — run/cancel/re-schedule must not fire `open-job`. Checked in Task 6's
   live check, because the node test environment cannot render HA's table.

---

### Task 1: History cap

**Files:**

- Modify: `frontend/src/state.ts`
- Test: `frontend/test/panel-state.test.ts`

**Interfaces:**

- Produces: `export const HISTORY_LIMIT = 15;` and
  `export function visibleHistory(history: Job[], filter: "all" | JobStatus, expanded: boolean, limit = HISTORY_LIMIT): { rows: Job[]; matching: number }`
  — `rows` keeps the input order (already newest first); `matching` is the filtered count before capping.

- [ ] **Step 1: Write the failing tests** in a new `describe("visibleHistory")` using the existing `job()` helper:

```ts
const many = (n: number, status: JobStatus = "done", prefix = "h") =>
  Array.from({ length: n }, (_, i) => job(`${prefix}${i}`, status));

it("caps at 15 when collapsed", () => {
  const r = visibleHistory(many(20), "all", false);
  expect(r.rows).toHaveLength(15);
  expect(ids(r.rows)[0]).toBe("h0");
  expect(r.matching).toBe(20);
});
it("returns all when expanded", () => expect(visibleHistory(many(20), "all", true).rows).toHaveLength(20));
it("exactly 15 is not capped", () => {
  const r = visibleHistory(many(15), "all", false);
  expect(r.rows).toHaveLength(15);
  expect(r.matching).toBe(15);
});
it("filters before capping", () => {
  const r = visibleHistory([...many(3, "failed", "f"), ...many(20)], "failed", false);
  expect(r.matching).toBe(3);
  expect(r.rows.every((j) => j.status === "failed")).toBe(true);
});
it("expanded with a new filter counts the new filter", () => {
  expect(visibleHistory([...many(18, "failed", "f"), ...many(2)], "failed", true)).toMatchObject({ matching: 18 });
});
```

- [ ] **Step 2: Run** `npm --prefix frontend test` — expected FAIL: `visibleHistory` is not exported.
- [ ] **Step 3: Implement** `visibleHistory` and `HISTORY_LIMIT` in `frontend/src/state.ts`. Rename the
      `upcomingLabel` docstring from "tab's label" to "card heading".
- [ ] **Step 4: Run** `npm --prefix frontend test` — expected PASS.

### Task 2: HA element loader

**Files:**

- Create: `frontend/src/ha-elements.ts`
- Test: `frontend/test/ha-elements.test.ts`

**Interfaces:**

- Produces:
  - `export const REQUIRED_ELEMENTS: readonly string[]` — the nine tags from Global Constraints.
  - `export interface ElementRegistry { get(tag: string): unknown; whenDefined(tag: string): Promise<unknown>; }`
  - `export async function waitForElements(registry: ElementRegistry, tags: readonly string[], timeoutMs: number): Promise<string[]>`
    — resolves to the tags still undefined after `timeoutMs` (empty array = all present). Never rejects.
  - `export function loadHaElements(timeoutMs = 10_000): Promise<string[]>` — memoised: every call returns the same
    promise. Triggers the config panel load (below), then `waitForElements(customElements, REQUIRED_ELEMENTS, timeoutMs)`.
    Any thrown error during triggering is swallowed (logged with `console.warn`) so the timeout path reports what is
    missing.

The trigger, verified against HA 2026.10.4 (`_getRoutes` and the config panel's `routerOptions.routes` are internal):

```ts
const ppr = document.createElement("partial-panel-resolver") as any;
ppr.hass = { panels: { config: { component_name: "config", url_path: "config" } } };
await ppr._getRoutes(ppr.hass.panels).routes.config.load();
await customElements.whenDefined("ha-panel-config");
const cfg = document.createElement("ha-panel-config") as any;
await cfg.routerOptions.routes.automation.load();
```

Skip the trigger entirely when every required tag is already defined.

- [ ] **Step 1: Write the failing tests** with a fake registry (no DOM in this environment):

```ts
function fakeRegistry(defined: string[], later: Record<string, number> = {}): ElementRegistry {
  const set = new Set(defined);
  return {
    get: (t) => (set.has(t) ? class {} : undefined),
    whenDefined: (t) =>
      set.has(t)
        ? Promise.resolve()
        : t in later
          ? new Promise((r) => setTimeout(() => (set.add(t), r(undefined)), later[t]))
          : new Promise(() => {})
  };
}

it("returns nothing missing when all defined", async () => {
  expect(await waitForElements(fakeRegistry(["a", "b"]), ["a", "b"], 50)).toEqual([]);
});
it("waits for elements that arrive before the timeout", async () => {
  expect(await waitForElements(fakeRegistry(["a"], { b: 10 }), ["a", "b"], 200)).toEqual([]);
});
it("names exactly the missing tags after the timeout", async () => {
  expect(await waitForElements(fakeRegistry(["a"], { c: 10 }), ["a", "b", "c"], 50)).toEqual(["b"]);
});
it("lists every required element", () => {
  expect([...REQUIRED_ELEMENTS].sort()).toEqual([
    "ha-button",
    "ha-card",
    "ha-data-table",
    "ha-dropdown",
    "ha-dropdown-item",
    "ha-filter-chip",
    "ha-icon-button",
    "ha-svg-icon",
    "hass-subpage"
  ]);
});
```

Memoisation (Review Focus 2): test it by stubbing `globalThis.customElements` with `fakeRegistry(REQUIRED_ELEMENTS)`
(`vi.stubGlobal`) so the trigger is skipped, and asserting `loadHaElements() === loadHaElements()`.

- [ ] **Step 2: Run** `npm --prefix frontend test` — expected FAIL: module not found.
- [ ] **Step 3: Implement** `frontend/src/ha-elements.ts` per the Interfaces block; module docstring states that it
      relies on HA frontend internals and which version it was verified against.
- [ ] **Step 4: Run** `npm --prefix frontend test` — expected PASS.

### Task 3: Upcoming card

**Files:**

- Modify: `frontend/package.json`, `frontend/package-lock.json` (add `@mdi/js`, exact pinned version, `dependencies`)
- Modify: `frontend/src/components/upcoming-table.ts`
- Modify: `frontend/src/types.ts` (only if a column type is needed, see below)

**Interfaces:**

- Consumes: nothing new; still fires `open-job`, `run-job`, `cancel-job` with `{ job }`.
- Produces: `<at-upcoming-table>` with the same properties (`hass`, `pending`, `running`, `now`, `isAdmin`), rendering
  `<ha-card .header=${upcomingLabel(...)}>` around `<ha-data-table>`.

`ha-data-table` contract (2026.10.4): `.hass`, `.columns` (object keyed by field: `title`, `template(row)`, `flex`,
`minWidth`, `type: "icon-button"`, `showNarrow`), `.data` (rows with an `id` field), `.noDataText`, `clickable`,
`auto-height`, `.narrow`; fires `row-click` with `detail.id` (does not bubble). Declare a local
`type DataTableColumns = Record<string, Record<string, unknown>>` in `types.ts`; do not import HA source.

- Columns: `when` (title "When", running rows show "Running…"), `summary` ("Job", flex 2), `source` ("Source"),
  `actions` (no title, `type: "icon-button"`, `showNarrow: true`): `ha-icon-button` with `mdiPlay` ("Run now", hidden
  under the existing `canRun` rule) and `mdiClose` ("Cancel"). Each button calls `e.stopPropagation()` before firing.
- `noDataText`: "Nothing scheduled."
- Remove all component CSS except `:host { display: block; }`.
- Add `narrow` property, passed through to the table.

- [ ] **Step 1: Install** `npm --prefix frontend install --save-exact @mdi/js` — `package.json` lists it under
      `dependencies` with an exact version.
- [ ] **Step 2: Rewrite** `upcoming-table.ts` per the bullets above.
- [ ] **Step 3: Run** `npm --prefix frontend run typecheck` and `npm --prefix frontend test` — expected both pass.

### Task 4: History card

**Files:**

- Modify: `frontend/src/components/history-table.ts`

**Interfaces:**

- Consumes: `visibleHistory`, `HISTORY_LIMIT` (Task 1); `DataTableColumns` (Task 3).
- Produces: `<at-history-table>` with properties `hass`, `history`, `now`, `narrow`; fires `open-job` and
  `reschedule-job` unchanged.

- `ha-card` with header "History". Below the header, a row of `ha-filter-chip`s (All, Done, Failed, Missed,
  Cancelled; `.selected` on the active one, `@click` sets the filter).
- `ha-data-table` columns: `status` (no title, icon via `ha-svg-icon`: `mdiCheckCircle` done, `mdiAlertCircle` failed,
  `mdiClockAlert` missed, `mdiCancel` cancelled, colour from `--success-color`, `--error-color`, `--warning-color`,
  `--secondary-text-color`; `title` attribute = status), `when` ("Time"), `summary` ("Job", flex 2), `result`
  ("Result"), `actions` (Re-schedule, `showNarrow: true`).
- Re-schedule keeps the inline `datetime-local` behaviour; its buttons become `ha-button` (`appearance="plain"`) and
  stop propagation.
- `noDataText`: "No history yet." when `history` is empty, otherwise "No jobs match this filter."
- Below the table, when `matching > HISTORY_LIMIT` and not expanded: `ha-button appearance="plain"` "Show all
  (`matching`)" which sets `expanded = true`. Expanded is a `@state()` that lives for the visit.
- Remove all component CSS except layout (`:host`, chip row gap/padding, the status colours, the footer alignment).

- [ ] **Step 1: Rewrite** `history-table.ts` per the bullets above.
- [ ] **Step 2: Run** `npm --prefix frontend run typecheck` and `npm --prefix frontend test` — expected both pass.

### Task 5: Panel shell

**Files:**

- Modify: `frontend/src/at-panel.ts`

**Interfaces:**

- Consumes: `loadHaElements` (Task 2), `<at-upcoming-table>` and `<at-history-table>` (Tasks 3–4).

- Remove `Tab`, `tab`, `tabButton`, `menuOpen`, `toggleMenu`, `fire_toggle_menu`, the hand-built header and all header,
  tab, add-pill and menu CSS.
- New `@state() private missing?: string[]` (undefined = still loading). In `start()`, `this.missing = await loadHaElements()`
  before subscribing; subscription still starts if elements are missing (jobs keep updating for when the user reloads).
- `render()`:
  - `missing === undefined`: render nothing (HA shows its own loading screen around the panel).
  - `missing.length`: a single plain block, "This panel needs an update for this Home Assistant version." followed by
    "Missing: " and the comma-joined tags. No HA elements in this branch.
  - Otherwise: `<hass-subpage main-page .hass .narrow .header=${this.title_}>` containing:
    - `slot="toolbar-icon"`: `<ha-dropdown @wa-select=…>` with a `slot="trigger"` `ha-icon-button` (`mdiDotsVertical`,
      label "More options") and `ha-dropdown-item`s `cancel-all` and `clear-history`. Cancel all keeps the two-step
      confirm: the first select sets `confirmCancelAll` and relabels the item "Confirm cancel all?".
    - the reconnecting notice and error banner, unchanged in behaviour (the error banner may become `ha-alert` only if
      it is in `REQUIRED_ELEMENTS`; it is not, so keep the plain markup).
    - `<div class="content">` with `<at-upcoming-table>` then `<at-history-table>`, both receiving `.narrow`.
    - `<ha-button slot="fab" size="l" @click=…>` with `<ha-svg-icon slot="start" .path=${mdiPlus}>` and "Add job".
  - The two dialogs stay outside `hass-subpage`, unchanged.
- CSS: `:host { display: block; height: 100%; }`; `.content` max-width 1000px, centred, 16px padding, 16px gap, and
  bottom padding ≥ 88px so the fab never covers the last row. Nothing else.

- [ ] **Step 1: Rewrite** `at-panel.ts` per the bullets above.
- [ ] **Step 2: Run** `npm --prefix frontend run typecheck` and `npm --prefix frontend test` — expected both pass.
- [ ] **Step 3: Run** `script/build-frontend` — expected a rebuilt `custom_components/at/frontend/at-panel.js`.

### Task 6: Spec, gates and live check

**Files:**

- Modify: `docs/superpowers/specs/2026-11-17-at-design.md` (§7.5 first bullet only)

- [ ] **Step 1: Update §7.5's "Header" bullet** to: the page uses HA's list-page elements (`hass-subpage`, `ha-card`,
      `ha-data-table`); Upcoming (n) and History are stacked cards; a ⋮ menu in the app bar holds "Cancel all" and
      "Clear history"; **+ Add job** is the floating button; History shows the 15 most recent rows with "Show all";
      if HA's elements fail to load, the panel shows only an update-needed message. Link the 2026-11-19 design.
- [ ] **Step 2: Run** `script/lint`, `script/type-check` and `script/test` — expected all exit 0 (`tests/test_panel.py`
      covers the panel registration and must still pass).
- [ ] **Step 3: Live check.** Check `script/ha status`; announce before restarting. Restart with the force-restart
      command from `AGENTS.md`, open the panel in a browser and confirm:
  - no "needs an update" message (all nine elements loaded); if one is missing, find which config route bundles it
    and add that route's `load()` to the trigger in Task 2, then rebuild;
  - light and dark theme both follow HA; the ☰ appears at phone width;
  - "+ Add job" sits bottom-right and opens the dialog; the last History row is not covered;
  - ▶, ✕ and Re-schedule do not also open the details dialog (Review Focus 5); a row click does;
  - Cancel all asks for confirmation; Clear history empties the History card;
  - with more than 15 history rows, "Show all (n)" appears and expands.
- [ ] **Step 4: Report** which checks passed in the live instance and which were not run, then offer a commit message
      (`feat(panel): …`) per `blueprint.commit-message`.
