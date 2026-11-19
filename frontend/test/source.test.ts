import { describe, expect, it } from "vitest";
import { historyDetail } from "../src/source";
import type { HomeAssistant, Job, JobStatus } from "../src/types";

function job(status: JobStatus, result: Partial<Job["result"]> = {}): Job {
  return {
    id: "j",
    kind: "action",
    status,
    due: "2026-11-18T12:00:00Z",
    created_at: "2026-11-18T10:00:00Z",
    finished_at: "2026-11-18T12:00:00Z",
    summary: "Turn on Porch",
    original_text: null,
    intent: null,
    action: [],
    raw_action: false,
    targets: { entity_ids: [], area_ids: [], floor_ids: [], names: [] },
    source: { via: "panel", user_id: null, device_id: null, agent_id: null },
    result: { error: null, cancelled_by: null, cancelled_user_id: null, cancelled_origin: null, ...result },
  };
}

const hass = {
  user: { id: "me", name: "Me" },
  states: {
    "person.brian": { state: "home", attributes: { friendly_name: "Brian", user_id: "u-brian" } },
    "automation.bedtime": { state: "on", attributes: { friendly_name: "Bedtime" } },
    "script.tidy_up": { state: "off", attributes: { friendly_name: "Tidy up" } },
  },
} as unknown as HomeAssistant;

const cancelled = (by: string | null, user: string | null = null, origin: string | null = null) =>
  historyDetail(job("cancelled", { cancelled_by: by, cancelled_user_id: user, cancelled_origin: origin }), hass);

describe("historyDetail", () => {
  it("shows the error for a failed job", () => {
    expect(historyDetail(job("failed", { error: "entity not found" }), hass)).toBe("entity not found");
  });

  it("explains a missed job", () => {
    expect(historyDetail(job("missed"), hass)).toBe("Home Assistant was off when it was due");
  });

  it("is empty for a done job", () => {
    expect(historyDetail(job("done"), hass)).toBe("");
  });

  it("names where and who for each channel", () => {
    expect(cancelled("panel", "u-brian")).toBe("Cancelled from the panel by Brian");
    expect(cancelled("voice", "u-brian")).toBe("Cancelled with voice by Brian");
    expect(cancelled("llm", "u-brian")).toBe("Cancelled with voice by Brian");
    expect(cancelled("todo", "u-brian")).toBe("Cancelled from the to-do list by Brian");
    expect(cancelled("service", "u-brian")).toBe("Cancelled by an action by Brian");
  });

  it("names the automation or script it came from", () => {
    expect(cancelled("service", null, "automation.bedtime")).toBe("Cancelled by automation Bedtime");
    expect(cancelled("service", "u-brian", "script.tidy_up")).toBe("Cancelled by script Tidy up by Brian");
    expect(cancelled("service", null, "automation.gone")).toBe("Cancelled by automation automation.gone");
  });

  it("falls back to the current user, then to no name", () => {
    expect(cancelled("panel", "me")).toBe("Cancelled from the panel by Me");
    expect(cancelled("panel", "u-unknown")).toBe("Cancelled from the panel");
  });

  it("handles jobs cancelled before who was recorded", () => {
    expect(cancelled("panel")).toBe("Cancelled from the panel");
    expect(cancelled(null)).toBe("Cancelled");
  });
});
