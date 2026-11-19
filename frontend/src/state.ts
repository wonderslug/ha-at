import type { Job, JobChangeKind, JobStatus, Snapshot } from "./types";

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

/** The Upcoming card's heading, with the number of pending jobs (spec 7.5). */
export function upcomingLabel(state: PanelState): string {
  return `Upcoming (${state.pending.length})`;
}

/** How many History rows show before "Show all" (spec 2026-11-19). */
export const HISTORY_LIMIT = 15;

/** The History rows to show for a status filter, capped unless expanded, and how many match in total. */
export function visibleHistory(
  history: Job[],
  filter: "all" | JobStatus,
  expanded: boolean,
  limit = HISTORY_LIMIT,
): { rows: Job[]; matching: number } {
  const matches = filter === "all" ? history : history.filter((j) => j.status === filter);
  return { rows: expanded ? matches : matches.slice(0, limit), matching: matches.length };
}
