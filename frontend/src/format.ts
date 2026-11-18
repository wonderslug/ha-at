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

function zoneOffsetMs(ts: number, timeZone: string): number {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hourCycle: "h23",
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "numeric",
    minute: "numeric",
    second: "numeric",
  }).formatToParts(new Date(ts));
  const get = (type: string) => Number(parts.find((p) => p.type === type)?.value);
  const asUtc = Date.UTC(get("year"), get("month") - 1, get("day"), get("hour"), get("minute"), get("second"));
  return asUtc - Math.floor(ts / 1000) * 1000;
}

/**
 * Interpret "YYYY-MM-DDTHH:MM" as wall-clock time in `timeZone`. Invalid input gives an Invalid Date.
 *
 * Same rule as the backend parser: a time in a spring-forward gap moves to the first valid minute
 * after it, and a repeated fall-back time is the first of the two.
 */
export function wallTimeToDate(value: string, timeZone: string): Date {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(value);
  if (!m) {
    return new Date(NaN);
  }
  const wall = Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]);
  for (let minute = 0; minute < 24 * 60; minute++) {
    const guess = wall + minute * 60_000;
    // The earlier of the two offsets around the guess gives the first occurrence of a repeated time.
    const offsets = [zoneOffsetMs(guess - 86_400_000, timeZone), zoneOffsetMs(guess + 86_400_000, timeZone)];
    const candidates = offsets.map((offset) => guess - offset).sort((a, b) => a - b);
    for (const ts of candidates) {
      if (ts + zoneOffsetMs(ts, timeZone) === guess) {
        return new Date(ts);
      }
    }
  }
  return new Date(wall - zoneOffsetMs(wall, timeZone));
}

/** Inverse of wallTimeToDate: "YYYY-MM-DDTHH:MM" wall-clock time of `date` in `timeZone`. */
export function dateToWallTime(date: Date, timeZone: string): string {
  const wall = new Date(date.getTime() + zoneOffsetMs(date.getTime(), timeZone));
  return wall.toISOString().slice(0, 16);
}
