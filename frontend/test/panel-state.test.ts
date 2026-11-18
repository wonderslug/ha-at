import { describe, expect, it } from "vitest";
import { applyChange, type PanelState } from "../src/state";
import { nextRetryDelay } from "../src/reconnect";
import type { Job, JobStatus } from "../src/types";

function job(id: string, status: JobStatus, due = "2026-11-18T12:00:00Z", finished: string | null = null): Job {
  return {
    id,
    kind: "action",
    status,
    due,
    created_at: "2026-11-18T10:00:00Z",
    finished_at: finished,
    summary: id,
    original_text: null,
    intent: null,
    action: [],
    raw_action: false,
    targets: { entity_ids: [], area_ids: [], floor_ids: [], names: [] },
    source: { via: "panel", user_id: null, device_id: null, agent_id: null },
    result: { error: null, cancelled_by: null },
  };
}

const empty: PanelState = { pending: [], running: [], history: [] };
const ids = (jobs: Job[]) => jobs.map((j) => j.id);

describe("applyChange", () => {
  it("adds a pending job sorted by due ascending", () => {
    let s = applyChange(empty, { kind: "added", job: job("b", "pending", "2026-11-18T13:00:00Z") });
    s = applyChange(s, { kind: "added", job: job("a", "pending", "2026-11-18T12:00:00Z") });
    expect(ids(s.pending)).toEqual(["a", "b"]);
  });

  it("moves a pending job to history at the top when it is done", () => {
    const old = job("old", "done", "2026-11-18T09:00:00Z", "2026-11-18T09:00:05Z");
    const s0: PanelState = { pending: [job("a", "pending")], running: [], history: [old] };
    const s1 = applyChange(s0, { kind: "updated", job: job("a", "done", "2026-11-18T12:00:00Z", "2026-11-18T12:00:01Z") });
    expect(s1.pending).toEqual([]);
    expect(ids(s1.history)).toEqual(["a", "old"]);
  });

  it("moves a job pending -> running -> history", () => {
    const s0: PanelState = { pending: [job("a", "pending")], running: [], history: [] };
    const s1 = applyChange(s0, { kind: "updated", job: job("a", "running") });
    expect(ids(s1.running)).toEqual(["a"]);
    expect(s1.pending).toEqual([]);
    const s2 = applyChange(s1, { kind: "updated", job: job("a", "failed", "2026-11-18T12:00:00Z", "2026-11-18T12:00:02Z") });
    expect(s2.running).toEqual([]);
    expect(ids(s2.history)).toEqual(["a"]);
  });

  it("moves a cancelled job to history", () => {
    const s0: PanelState = { pending: [job("a", "pending")], running: [], history: [] };
    const s1 = applyChange(s0, { kind: "updated", job: job("a", "cancelled", "2026-11-18T12:00:00Z", "2026-11-18T11:00:00Z") });
    expect(s1.pending).toEqual([]);
    expect(s1.history[0].status).toBe("cancelled");
  });

  it("removed drops the job from every list", () => {
    const s0: PanelState = {
      pending: [job("p", "pending")],
      running: [job("r", "running")],
      history: [job("h", "done", "x", "2026-11-18T09:00:00Z")],
    };
    for (const id of ["p", "r", "h"]) {
      const s = applyChange(s0, { kind: "removed", job: job(id, "done") });
      expect([...s.pending, ...s.running, ...s.history].map((j) => j.id)).not.toContain(id);
    }
  });

  it("does not mutate the input", () => {
    const s0: PanelState = { pending: [job("a", "pending")], running: [], history: [] };
    applyChange(s0, { kind: "updated", job: job("a", "done", "x", "2026-11-18T12:00:00Z") });
    expect(ids(s0.pending)).toEqual(["a"]);
  });
});

describe("nextRetryDelay", () => {
  it("backs off from 1s and caps", () => {
    expect(nextRetryDelay(0)).toBe(1000);
    expect(nextRetryDelay(1)).toBe(2000);
    expect(nextRetryDelay(2)).toBe(4000);
    expect(nextRetryDelay(7)).toBe(30000);
  });
  it("never gives up and stays at the cap", () => {
    expect(nextRetryDelay(9)).toBe(30000);
    expect(nextRetryDelay(1000)).toBe(30000);
  });
});
