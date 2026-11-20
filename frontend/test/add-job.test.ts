import { describe, expect, it } from "vitest";
import { buildPickedAction, fromServiceControl, isFuture, parseJsonObject, parseRawAction, quickDue, type PickedInput } from "../src/add-job";
import shapes from "./picked-shapes.json";

describe("shared picked shapes", () => {
  it.each(shapes)("builds $expected", ({ input, expected }) => {
    expect(buildPickedAction(input as PickedInput)).toEqual(expected);
  });
});

describe("isFuture", () => {
  const now = new Date("2026-11-18T18:00:00Z");
  it("requires a valid later date", () => {
    expect(isFuture(new Date("2026-11-18T18:00:01Z"), now)).toBe(true);
    expect(isFuture(new Date("2026-11-18T17:59:00Z"), now)).toBe(false);
    expect(isFuture(now, now)).toBe(false);
    expect(isFuture(new Date(NaN), now)).toBe(false);
  });
});

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

describe("fromServiceControl", () => {
  it("is undefined until an action is chosen", () => {
    expect(fromServiceControl(undefined)).toBeUndefined();
    expect(fromServiceControl({})).toBeUndefined();
  });
  it("omits an empty target and data", () => {
    expect(fromServiceControl({ action: "light.turn_on", target: {}, data: {} })).toEqual([{ action: "light.turn_on" }]);
  });
  it("drops empty target values, and the target when nothing is left", () => {
    expect(fromServiceControl({ action: "light.turn_on", target: { entity_id: [], device_id: "" } })).toEqual([
      { action: "light.turn_on" },
    ]);
    expect(fromServiceControl({ action: "light.turn_on", target: { entity_id: [], area_id: ["kitchen"] } })).toEqual([
      { action: "light.turn_on", target: { area_id: ["kitchen"] } },
    ]);
  });
  it("keeps a target and data", () => {
    expect(
      fromServiceControl({ action: "light.turn_on", target: { entity_id: ["light.a"] }, data: { brightness_pct: 80 } }),
    ).toEqual([{ action: "light.turn_on", target: { entity_id: ["light.a"] }, data: { brightness_pct: 80 } }]);
  });
});
