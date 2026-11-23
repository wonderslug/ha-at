// @vitest-environment happy-dom
import { type LitElement, render, type TemplateResult } from "lit";
import { afterEach, describe, expect, it } from "vitest";
import "../src/components/history-table";
import "../src/components/upcoming-table";
import { wallTimeToDate } from "../src/format";
import type { DataTableColumns, HomeAssistant, Job, JobStatus } from "../src/types";
import { enHass, enLocalize } from "./en-localize";

function job(id: string, status: JobStatus, extra: Partial<Job> = {}): Job {
  return {
    id,
    kind: "action",
    status,
    due: "2026-11-18T12:00:00Z",
    created_at: "2026-11-18T10:00:00Z",
    finished_at: status === "pending" || status === "running" ? null : "2026-11-18T12:00:00Z",
    summary: `job ${id}`,
    original_text: null,
    intent: null,
    action: [],
    raw_action: false,
    targets: { entity_ids: [], area_ids: [], floor_ids: [], names: [] },
    source: { via: "panel", user_id: null, device_id: null, agent_id: null },
    result: { error: null, cancelled_by: null },
    ...extra,
  };
}

const HASS = enHass({ config: { time_zone: "America/Chicago" }, states: {}, user: { is_admin: false } } as unknown as Partial<HomeAssistant>);

async function mount<T extends LitElement>(tag: string, props: Record<string, unknown>): Promise<T> {
  const el = document.createElement(tag) as T;
  Object.assign(el, { hass: HASS, localize: enLocalize, ...props });
  document.body.append(el);
  await el.updateComplete;
  return el;
}

interface Table extends HTMLElement {
  columns: DataTableColumns;
  data: { id: string; when: string; job: Job }[];
}

function table(el: LitElement): Table {
  return el.shadowRoot!.querySelector("ha-data-table") as Table;
}

function actions(el: LitElement, rowIndex: number): HTMLElement {
  const t = table(el);
  const template = t.columns.actions.template as (row: unknown) => TemplateResult;
  const cell = document.createElement("div");
  render(template(t.data[rowIndex]), cell);
  return cell;
}

function buttons(cell: HTMLElement, tag: string): { label: string; el: HTMLElement }[] {
  return [...cell.querySelectorAll<HTMLElement>(tag)].map((el) => ({
    label: (el as HTMLElement & { label?: string }).label ?? el.textContent?.trim() ?? "",
    el,
  }));
}

function nextEvent(el: EventTarget, name: string): Promise<CustomEvent> {
  return new Promise((resolve) => el.addEventListener(name, (e) => resolve(e as CustomEvent), { once: true }));
}

afterEach(() => {
  document.body.replaceChildren();
});

describe("at-upcoming-table", () => {
  it("lists running jobs first and gives them no actions", async () => {
    const el = await mount("at-upcoming-table", { pending: [job("p", "pending")], running: [job("r", "running")] });
    expect(table(el).data.map((r) => r.id)).toEqual(["r", "p"]);
    expect(table(el).data[0].when).toBe("Running…");
    expect(buttons(actions(el, 0), "ha-icon-button")).toEqual([]);
  });

  it("hides run now from a non-admin for a raw action but keeps cancel", async () => {
    const raw = job("raw", "pending", { raw_action: true });
    const picked = job("picked", "pending");
    const el = await mount("at-upcoming-table", { pending: [raw, picked], isAdmin: false });
    expect(buttons(actions(el, 0), "ha-icon-button").map((b) => b.label)).toEqual(["Cancel"]);
    expect(buttons(actions(el, 1), "ha-icon-button").map((b) => b.label)).toEqual(["Run now", "Cancel"]);
  });

  it("shows run now to an admin for a raw action", async () => {
    const el = await mount("at-upcoming-table", { pending: [job("raw", "pending", { raw_action: true })], isAdmin: true });
    expect(buttons(actions(el, 0), "ha-icon-button").map((b) => b.label)).toEqual(["Run now", "Cancel"]);
  });

  it("fires cancel-job and run-job with the row's job", async () => {
    const pending = job("p", "pending");
    const el = await mount("at-upcoming-table", { pending: [pending] });
    const [run, cancel] = buttons(actions(el, 0), "ha-icon-button");

    const cancelled = nextEvent(el, "cancel-job");
    cancel.el.click();
    expect((await cancelled).detail.job).toBe(pending);

    const ran = nextEvent(el, "run-job");
    run.el.click();
    expect((await ran).detail.job).toBe(pending);
  });

  it("opens a job when its row is clicked", async () => {
    const pending = job("p", "pending");
    const el = await mount("at-upcoming-table", { pending: [pending] });
    const opened = nextEvent(el, "open-job");
    table(el).dispatchEvent(new CustomEvent("row-click", { detail: { id: "p" } }));
    expect((await opened).detail.job).toBe(pending);
  });
});

describe("at-history-table", () => {
  it("filters by status when a chip is clicked", async () => {
    const el = await mount("at-history-table", { history: [job("d", "done"), job("f", "failed")] });
    expect(table(el).data.map((r) => r.id).sort()).toEqual(["d", "f"]);

    const failed = [...el.shadowRoot!.querySelectorAll<HTMLElement & { label: string }>("ha-filter-chip")].find(
      (chip) => chip.label === "Failed",
    );
    failed!.click();
    await el.updateComplete;
    expect(table(el).data.map((r) => r.id)).toEqual(["f"]);
  });

  it("re-schedules a finished job at the wall time entered, in the home's time zone", async () => {
    const done = job("d", "done");
    const el = await mount("at-history-table", { history: [done] });

    buttons(actions(el, 0), "ha-button")
      .find((b) => b.label === "Re-schedule")!
      .el.click();
    await el.updateComplete;

    const editing = actions(el, 0);
    const input = editing.querySelector("input")!;
    input.value = "2026-11-20T07:30";
    input.dispatchEvent(new Event("input"));
    await el.updateComplete;

    const rescheduled = nextEvent(el, "reschedule-job");
    buttons(actions(el, 0), "ha-button")
      .find((b) => b.label === "Save")!
      .el.click();
    const { detail } = await rescheduled;
    expect(detail.job).toBe(done);
    expect(detail.due).toBe(wallTimeToDate("2026-11-20T07:30", "America/Chicago").toISOString());
    expect(detail.due).toBe("2026-11-20T13:30:00.000Z");
  });
});
