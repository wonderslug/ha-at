import { describe, expect, it } from "vitest";
import { buildPickedAction, parseJsonObject, parseRawAction, quickDue } from "../src/add-job";

describe("buildPickedAction", () => {
  it("builds homeassistant verbs with an entity list", () => {
    expect(buildPickedAction({ targetEntityIds: ["light.porch"], verb: "turn_on" })).toEqual([
      { action: "homeassistant.turn_on", target: { entity_id: ["light.porch"] } },
    ]);
    expect(buildPickedAction({ targetEntityIds: ["light.a", "fan.b"], verb: "toggle" })).toEqual([
      { action: "homeassistant.toggle", target: { entity_id: ["light.a", "fan.b"] } },
    ]);
  });
  it("builds a script run without variables", () => {
    expect(buildPickedAction({ script: "script.movie" })).toEqual([
      { action: "script.turn_on", target: { entity_id: "script.movie" } },
    ]);
  });
  it("builds a script run with variables", () => {
    expect(buildPickedAction({ script: "script.movie", variables: { level: 3 } })).toEqual([
      { action: "script.turn_on", target: { entity_id: "script.movie" }, data: { variables: { level: 3 } } },
    ]);
  });
  it("omits empty variables", () => {
    expect(buildPickedAction({ script: "script.movie", variables: {} })).toEqual([
      { action: "script.turn_on", target: { entity_id: "script.movie" } },
    ]);
  });
  it("builds an automation trigger", () => {
    expect(buildPickedAction({ automation: "automation.night" })).toEqual([
      { action: "automation.trigger", target: { entity_id: "automation.night" } },
    ]);
  });
});

describe("quickDue", () => {
  const now = new Date("2026-11-18T18:00:00Z");
  it("gives seconds", () => {
    expect(quickDue("+15m", now)).toEqual({ delay_seconds: 900 });
    expect(quickDue("+1h", now)).toEqual({ delay_seconds: 3600 });
  });
});

describe("parseJsonObject", () => {
  it("treats blank as empty", () => {
    expect(parseJsonObject("  ")).toEqual({ ok: true, value: {} });
  });
  it("accepts an object", () => {
    expect(parseJsonObject('{"a": 1}')).toEqual({ ok: true, value: { a: 1 } });
  });
  it("rejects bad JSON and non-objects", () => {
    expect(parseJsonObject("{").ok).toBe(false);
    expect(parseJsonObject("[1]").ok).toBe(false);
    expect(parseJsonObject("5").ok).toBe(false);
  });
});

describe("parseRawAction", () => {
  it("accepts a list of objects", () => {
    expect(parseRawAction('[{"action": "light.turn_on"}]')).toEqual({ ok: true, value: [{ action: "light.turn_on" }] });
  });
  it("rejects an empty list, non-lists and bad JSON", () => {
    expect(parseRawAction("[]").ok).toBe(false);
    expect(parseRawAction('{"a":1}').ok).toBe(false);
    expect(parseRawAction("[1]").ok).toBe(false);
    expect(parseRawAction("nope").ok).toBe(false);
  });
});
