/** Pure formatting helpers; the time zone and locale are always passed in. */

const HOUR_MS = 3_600_000;
const DAY_MS = 86_400_000;

/** "27:41" for a due time less than an hour away, otherwise "". */
export function formatCountdown(dueMs: number, nowMs: number): string {
  const remaining = dueMs - nowMs;
  if (remaining < 0 || remaining >= HOUR_MS) {
    return "";
  }
  const totalSeconds = Math.floor(remaining / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function dayKey(date: Date, locale: string, timeZone: string): string {
  return new Intl.DateTimeFormat(locale, { timeZone, year: "numeric", month: "numeric", day: "numeric" }).format(date);
}

/** The time today, "Tue 6:00 AM" within 7 days, otherwise "Dec 3, 8:00 AM". */
export function formatWhen(due: Date, now: Date, locale: string, timeZone: string): string {
  const time = new Intl.DateTimeFormat(locale, { timeZone, hour: "numeric", minute: "2-digit" }).format(due);
  if (dayKey(due, locale, timeZone) === dayKey(now, locale, timeZone)) {
    return time;
  }
  const diff = due.getTime() - now.getTime();
  if (diff > 0 && diff < 7 * DAY_MS) {
    const weekday = new Intl.DateTimeFormat(locale, { timeZone, weekday: "short" }).format(due);
    return `${weekday} ${time}`;
  }
  const date = new Intl.DateTimeFormat(locale, { timeZone, month: "short", day: "numeric" }).format(due);
  return `${date}, ${time}`;
}
