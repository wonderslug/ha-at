import { describe, expect, it } from "vitest";
import { dateToWallTime, formatCountdown, formatWhen, wallTimeToDate } from "../src/format";

const TZ = "America/Chicago";
const LOCALE = "en-US";
// 2026-11-18 18:00 UTC is 12:00 PM in Chicago (CST, UTC-6).
const now = new Date("2026-11-18T18:00:00Z");

describe("formatCountdown", () => {
  it("shows minutes and seconds under an hour", () => {
    expect(formatCountdown(now.getTime() + 1_661_000, now.getTime())).toBe("27:41");
  });
  it("is empty at an hour or more", () => {
    expect(formatCountdown(now.getTime() + 3_600_001, now.getTime())).toBe("");
  });
  it("is empty when the job is overdue", () => {
    expect(formatCountdown(now.getTime() - 1000, now.getTime())).toBe("");
  });
});

describe("formatWhen", () => {
  it("shows only the time today", () => {
    expect(formatWhen(new Date("2026-11-19T05:00:00Z"), now, LOCALE, TZ)).toBe("11:00 PM");
  });
  it("shows the weekday within 7 days", () => {
    // Tue 2026-11-24 12:00 UTC = 6:00 AM in Chicago.
    expect(formatWhen(new Date("2026-11-24T12:00:00Z"), now, LOCALE, TZ)).toBe("Tue 6:00 AM");
  });
  it("shows the date after that", () => {
    // Dec 3 14:00 UTC = 8:00 AM in Chicago.
    expect(formatWhen(new Date("2026-12-03T14:00:00Z"), now, LOCALE, TZ)).toBe("Dec 3, 8:00 AM");
  });
});

describe("wallTimeToDate", () => {
  it("Chicago normal day (CST)", () => {
    expect(wallTimeToDate("2026-11-18T12:00", "America/Chicago").toISOString()).toBe("2026-11-18T18:00:00.000Z");
  });
  it("Berlin summer (CEST)", () => {
    expect(wallTimeToDate("2026-07-01T09:30", "Europe/Berlin").toISOString()).toBe("2026-07-01T07:30:00.000Z");
  });
  it("US DST change day, before and after the switch", () => {
    // 2026-03-08: Chicago springs forward at 02:00 CST.
    expect(wallTimeToDate("2026-03-08T01:30", "America/Chicago").toISOString()).toBe("2026-03-08T07:30:00.000Z");
    expect(wallTimeToDate("2026-03-08T03:30", "America/Chicago").toISOString()).toBe("2026-03-08T08:30:00.000Z");
  });
  it("moves a time in the spring-forward gap to the first valid minute after it", () => {
    // 02:30 does not exist on 2026-03-08 in Chicago; the parser's rule gives 03:00 CDT (08:00 UTC).
    expect(wallTimeToDate("2026-03-08T02:30", "America/Chicago").toISOString()).toBe("2026-03-08T08:00:00.000Z");
  });
  it("round-trips through dateToWallTime", () => {
    const d = wallTimeToDate("2026-11-18T12:00", "Europe/Berlin");
    expect(dateToWallTime(d, "Europe/Berlin")).toBe("2026-11-18T12:00");
  });
  it("rejects garbage", () => {
    expect(Number.isNaN(wallTimeToDate("", "UTC").getTime())).toBe(true);
  });
});
