import { describe, expect, it } from "vitest";
import { formatCountdown, formatWhen } from "../src/format";

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
