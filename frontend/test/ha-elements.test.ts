import { afterEach, describe, expect, it, vi } from "vitest";
import {
  type ElementRegistry,
  loadElements,
  loadHaElements,
  loadPickerElements,
  PICKER_ELEMENTS,
  pickerElementsDefined,
  REQUIRED_ELEMENTS,
  runLoadSteps,
  waitForElements,
} from "../src/ha-elements";

function fakeRegistry(defined: readonly string[], later: Record<string, number> = {}): ElementRegistry {
  const set = new Set(defined);
  return {
    get: (t) => (set.has(t) ? class {} : undefined),
    whenDefined: (t) =>
      set.has(t)
        ? Promise.resolve()
        : t in later
          ? new Promise((r) => setTimeout(() => (set.add(t), r(undefined)), later[t]))
          : new Promise(() => undefined),
  };
}

describe("waitForElements", () => {
  it("returns nothing missing when all are defined", async () => {
    expect(await waitForElements(fakeRegistry(["a", "b"]), ["a", "b"], 50)).toEqual([]);
  });

  it("waits for elements that arrive before the timeout", async () => {
    expect(await waitForElements(fakeRegistry(["a"], { b: 10 }), ["a", "b"], 200)).toEqual([]);
  });

  it("names exactly the missing tags after the timeout", async () => {
    expect(await waitForElements(fakeRegistry(["a"], { c: 10 }), ["a", "b", "c"], 50)).toEqual(["b"]);
  });
});

describe("REQUIRED_ELEMENTS", () => {
  it("lists every element the panel renders", () => {
    expect([...REQUIRED_ELEMENTS].sort()).toEqual([
      "ha-button",
      "ha-card",
      "ha-data-table",
      "ha-dropdown",
      "ha-dropdown-item",
      "ha-filter-chip",
      "ha-icon-button",
      "ha-svg-icon",
      "hass-subpage",
    ]);
  });
});

describe("loadHaElements", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("returns the same promise on every call", async () => {
    vi.stubGlobal("customElements", fakeRegistry(REQUIRED_ELEMENTS));
    const first = loadHaElements();
    expect(loadHaElements()).toBe(first);
    expect(await first).toEqual([]);
  });
});

describe("loadPickerElements", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("lists the elements the Pick it tab renders", () => {
    expect(PICKER_ELEMENTS).toEqual(["ha-service-control", "ha-selector"]);
  });

  it("returns the same promise on every call", async () => {
    vi.stubGlobal("customElements", fakeRegistry(PICKER_ELEMENTS));
    const first = loadPickerElements();
    expect(loadPickerElements()).toBe(first);
    expect(await first).toEqual([]);
  });
});

describe("pickerElementsDefined", () => {
  it("needs every picker element", () => {
    expect(pickerElementsDefined(fakeRegistry(PICKER_ELEMENTS))).toBe(true);
    expect(pickerElementsDefined(fakeRegistry(["ha-service-control"]))).toBe(false);
  });
});

describe("runLoadSteps", () => {
  function defining(set: Set<string>, tags: string[], calls: string[], name: string) {
    return async () => {
      calls.push(name);
      tags.forEach((t) => set.add(t));
    };
  }

  function liveRegistry(set: Set<string>): ElementRegistry {
    return { get: (t) => (set.has(t) ? class {} : undefined), whenDefined: () => new Promise(() => undefined) };
  }

  it("tries the steps in order and stops once every tag is defined", async () => {
    const set = new Set<string>();
    const calls: string[] = [];
    const steps = [defining(set, ["a"], calls, "one"), defining(set, ["b"], calls, "two"), defining(set, [], calls, "three")];
    await runLoadSteps(liveRegistry(set), ["a", "b"], steps, 50);
    expect(calls).toEqual(["one", "two"]);
  });

  it("runs no step when everything is already defined", async () => {
    const calls: string[] = [];
    await runLoadSteps(liveRegistry(new Set(["a"])), ["a"], [defining(new Set(), [], calls, "one")], 50);
    expect(calls).toEqual([]);
  });

  it("continues after a step throws, without logging", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    const set = new Set<string>();
    const calls: string[] = [];
    const broken = async () => {
      calls.push("broken");
      throw new Error("no such route");
    };
    await runLoadSteps(liveRegistry(set), ["a"], [broken, defining(set, ["a"], calls, "two")], 50);
    expect(calls).toEqual(["broken", "two"]);
    expect(warn).not.toHaveBeenCalled();
    warn.mockRestore();
  });

  it("gives a hung step only its own time", async () => {
    const set = new Set<string>();
    const calls: string[] = [];
    const hung = () => new Promise<void>(() => calls.push("hung"));
    await runLoadSteps(liveRegistry(set), ["a"], [hung, defining(set, ["a"], calls, "two")], 20);
    expect(calls).toEqual(["hung", "two"]);
    expect(set.has("a")).toBe(true);
  });
});

describe("loadElements", () => {
  afterEach(() => vi.restoreAllMocks());

  it("reports missing tags when the trigger never settles", async () => {
    vi.spyOn(console, "warn").mockImplementation(() => undefined);
    const hung = () => new Promise<void>(() => undefined);
    expect(await loadElements(fakeRegistry(["a"]), hung, ["a", "b"], 50)).toEqual(["b"]);
  });

  it("reports missing tags when the trigger throws", async () => {
    vi.spyOn(console, "warn").mockImplementation(() => undefined);
    const broken = () => Promise.reject(new Error("renamed"));
    expect(await loadElements(fakeRegistry(["a"]), broken, ["a", "b"], 50)).toEqual(["b"]);
  });

  it("logs the missing tags", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    await loadElements(fakeRegistry(["a"]), () => Promise.resolve(), ["a", "b"], 20);
    expect(warn.mock.calls.flat().join(" ")).toContain("b");
  });

  it("skips the trigger when everything is defined", async () => {
    const trigger = vi.fn(() => Promise.resolve());
    expect(await loadElements(fakeRegistry(["a"]), trigger, ["a"], 20)).toEqual([]);
    expect(trigger).not.toHaveBeenCalled();
  });
});
