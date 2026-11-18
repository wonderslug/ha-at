export const BASE_DELAY_MS = 1000;
export const MAX_DELAY_MS = 30000;

/** Delay before retry number `attempt` (0-based): doubling from 1 s, capped at 30 s, never gives up. */
export function nextRetryDelay(attempt: number): number {
  return Math.min(BASE_DELAY_MS * 2 ** Math.min(attempt, 10), MAX_DELAY_MS);
}
