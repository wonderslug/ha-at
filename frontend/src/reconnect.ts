export const BASE_DELAY_MS = 1000;
export const MAX_DELAY_MS = 30000;
export const MAX_ATTEMPTS = 9;

/** Delay before retry number `attempt` (0-based), or null once retries are exhausted. */
export function nextRetryDelay(attempt: number): number | null {
  if (attempt >= MAX_ATTEMPTS) {
    return null;
  }
  return Math.min(BASE_DELAY_MS * 2 ** attempt, MAX_DELAY_MS);
}
