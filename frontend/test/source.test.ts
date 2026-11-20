import { describe, expect, it } from "vitest";
import { historyDetail, sourceLabel } from "../src/source";
import type { HomeAssistant, Job, JobStatus } from "../src/types";

function job(status: JobStatus, result: Partial<Job["result"]> = {}, source: Partial<Job["source"]> = {}): Job {
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
    source: { via: "panel", user_id: null, device_id: null, agent_id: null, origin: null, ...source },
    result: {
      error: null,
      cancelled_by: null,
      cancelled_user_id: null,
      cancelled_origin: null,
      cancelled_device_id: null,
      ...result,
    },
  };
}

const hass = {
  user: { id: "me", name: "Me" },
  devices: {
    "sat-1": { name: "Satellite1", name_by_user: "Kitchen satellite" },
    phone: { name: "Brian's phone", name_by_user: null },
  },
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
    expect(cancelled("panel", "u-brian")).toBe("Cancelled in the panel by Brian");
    expect(cancelled("voice", "u-brian")).toBe("Cancelled from Assist by Brian");
    expect(cancelled("llm", "u-brian")).toBe("Cancelled from Assist by Brian");
    expect(cancelled("todo", "u-brian")).toBe("Cancelled from the to-do list by Brian");
    expect(cancelled("service", "u-brian")).toBe("Cancelled by an action by Brian");
    expect(cancelled("service", null)).toBe("Cancelled by an action");
  });

  it("names the satellite an Assist cancel came from", () => {
    const viaDevice = (device: string, user: string | null = null) =>
      historyDetail(
        job("cancelled", { cancelled_by: "voice", cancelled_user_id: user, cancelled_device_id: device }),
        hass,
      );
    expect(viaDevice("sat-1", "u-brian")).toBe("Cancelled from Assist · Kitchen satellite by Brian");
    expect(viaDevice("deleted")).toBe("Cancelled from Assist");
  });

  it("names the device without a person when nobody is known", () => {
    const fromDevice = (by: string) =>
      historyDetail(job("cancelled", { cancelled_by: by, cancelled_user_id: null, cancelled_device_id: "sat-1" }), hass);
    expect(fromDevice("voice")).toBe("Cancelled from Assist · Kitchen satellite");
    expect(fromDevice("llm")).toBe("Cancelled from Assist · Kitchen satellite");
  });

  it("names the device an LLM cancel came from, with the person", () => {
    expect(
      historyDetail(job("cancelled", { cancelled_by: "llm", cancelled_user_id: "u-brian", cancelled_device_id: "phone" }), hass),
    ).toBe("Cancelled from Assist · Brian's phone by Brian");
  });

  it("names the automation or script it came from", () => {
    expect(cancelled("service", null, "automation.bedtime")).toBe("Cancelled by automation Bedtime");
    expect(cancelled("service", "u-brian", "script.tidy_up")).toBe("Cancelled by script Tidy up by Brian");
    expect(cancelled("service", null, "automation.gone")).toBe("Cancelled by automation automation.gone");
  });

  it("falls back to the current user, then to no name", () => {
    expect(cancelled("panel", "me")).toBe("Cancelled in the panel by Me");
    expect(cancelled("panel", "u-unknown")).toBe("Cancelled in the panel");
  });

  it("handles jobs cancelled before who was recorded", () => {
    expect(cancelled("panel")).toBe("Cancelled in the panel");
    expect(cancelled(null)).toBe("Cancelled");
  });
});

describe("sourceLabel", () => {
  const src = (source: Partial<Job["source"]>) => sourceLabel(job("pending", {}, source), hass);

  it("calls every Assist path Assist", () => {
    expect(src({ via: "voice", device_id: "sat-1" })).toBe("Assist · Kitchen satellite");
    expect(src({ via: "voice", device_id: "sat-1", user_id: "u-brian" })).toBe("Assist · Kitchen satellite · Brian");
    expect(src({ via: "voice", user_id: "u-brian" })).toBe("Assist · Brian");
    expect(src({ via: "voice", device_id: "phone", user_id: "u-brian" })).toBe("Assist · Brian's phone · Brian");
    expect(src({ via: "llm", user_id: "u-brian" })).toBe("Assist · Brian");
    expect(src({ via: "voice" })).toBe("Assist");
  });

  it("names the panel action and the to-do list", () => {
    expect(src({ via: "panel", user_id: "u-brian" })).toBe("Add job · Brian");
    expect(src({ via: "reschedule", user_id: "u-brian" })).toBe("Reschedule · Brian");
    expect(src({ via: "todo", user_id: "u-brian" })).toBe("To-do list · Brian");
  });

  it("names the automation or script behind an action", () => {
    expect(src({ via: "service", origin: "automation.bedtime" })).toBe("Automation · Bedtime");
    expect(src({ via: "service", origin: "script.tidy_up", user_id: "u-brian" })).toBe("Script · Tidy up · Brian");
    expect(src({ via: "service", origin: "automation.gone" })).toBe("Automation · automation.gone");
    expect(src({ via: "service", user_id: "u-brian" })).toBe("Action · Brian");
    expect(src({ via: "service" })).toBe("Action");
  });

  it("leaves out what it cannot resolve", () => {
    expect(src({ via: "voice", device_id: "deleted" })).toBe("Assist");
    expect(src({ via: "panel", user_id: "stranger" })).toBe("Add job");
    expect(src({ via: "panel", user_id: "me" })).toBe("Add job · Me");
  });
});
