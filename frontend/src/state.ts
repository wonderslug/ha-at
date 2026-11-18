import type { Job, JobChangeKind, Snapshot } from "./types";

export type PanelState = Snapshot;

const byDue = (a: Job, b: Job) => Date.parse(a.due) - Date.parse(b.due);
const finishedMs = (j: Job) => Date.parse(j.finished_at ?? j.due);
const byFinishedDesc = (a: Job, b: Job) => finishedMs(b) - finishedMs(a);

/** Sort a snapshot's lists into display order. */
export function normalize(s: Snapshot): PanelState {
  return {
    pending: [...s.pending].sort(byDue),
    running: [...s.running].sort(byDue),
    history: [...s.history].sort(byFinishedDesc),
  };
}

/** Apply one `change` event: move the job to the list matching its status. Pure. */
export function applyChange(state: PanelState, change: { kind: JobChangeKind; job: Job }): PanelState {
  const { job } = change;
  const without = (jobs: Job[]) => jobs.filter((j) => j.id !== job.id);
  const next: PanelState = {
    pending: without(state.pending),
    running: without(state.running),
    history: without(state.history),
  };
  if (change.kind !== "removed") {
    if (job.status === "pending") {
      next.pending.push(job);
    } else if (job.status === "running") {
      next.running.push(job);
    } else {
      next.history.push(job);
    }
  }
  return normalize(next);
}
