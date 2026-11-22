// @vitest-environment happy-dom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import "../src/components/add-job-dialog";
import type { PickAction } from "../src/components/pick-action";
import type { AddJobDialog } from "../src/components/add-job-dialog";
import type { HomeAssistant } from "../src/types";
import { enHass, enLocalize } from "./en-localize";

const loader = vi.hoisted(() => ({ next: () => Promise.resolve<string[]>([]), defined: true }));
vi.mock("../src/ha-elements", () => ({ loadPickerElements: () => loader.next(), pickerElementsDefined: () => loader.defined }));

customElements.define("ha-service-control", class extends HTMLElement {});
customElements.define("ha-selector", class extends HTMLElement {});

function pending() {
  let resolve!: (missing: string[]) => void;
  const promise = new Promise<string[]>((r) => (resolve = r));
  return { promise, resolve };
}

type Send = (msg: { type: string; text?: string }) => Promise<unknown>;

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => (resolve = r));
  return { promise, resolve };
}

const PARSED = (summary: string) => ({ ok: true, due: "2026-11-20T12:00:00Z", summary });

async function openDialog(send: Send): Promise<AddJobDialog> {
  const el = document.createElement("at-add-job-dialog");
  el.hass = enHass({ states: {}, connection: { sendMessagePromise: send } } as unknown as Partial<HomeAssistant>);
  el.localize = enLocalize;
  document.body.append(el);
  el.open = true;
  await el.updateComplete;
  return el;
}

function $(el: AddJobDialog, selector: string): HTMLElement {
  return el.shadowRoot!.querySelector<HTMLElement>(selector)!;
}

function type(el: AddJobDialog, text: string) {
  const input = $(el, "#text") as HTMLInputElement;
  input.value = text;
  input.dispatchEvent(new Event("input"));
}

function press(key: string, shiftKey = false) {
  window.dispatchEvent(new KeyboardEvent("keydown", { key, shiftKey, cancelable: true }));
}

function preview(el: AddJobDialog): string {
  return el.shadowRoot!.querySelector(".preview")?.textContent ?? "";
}

beforeEach(() => {
  vi.useFakeTimers();
  loader.next = () => Promise.resolve([]);
  loader.defined = true;
});

afterEach(() => {
  vi.useRealTimers();
  document.body.replaceChildren();
});

describe("at-add-job-dialog typing", () => {
  it("parses once, 300 ms after the last keystroke, with the final text", async () => {
    const send = vi.fn<Send>(async (msg) => PARSED(msg.text ?? ""));
    const el = await openDialog(send);

    type(el, "turn");
    await vi.advanceTimersByTimeAsync(200);
    type(el, "turn on the porch light at 11pm");
    await vi.advanceTimersByTimeAsync(299);
    expect(send).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(1);
    expect(send).toHaveBeenCalledTimes(1);
    expect(send.mock.calls[0][0]).toEqual({ type: "at/parse", text: "turn on the porch light at 11pm" });
  });

  it("ignores a slow answer for text that has since changed", async () => {
    const first = deferred<unknown>();
    const send = vi.fn<Send>((msg) => (msg.text === "old" ? first.promise : Promise.resolve(PARSED("New"))));
    const el = await openDialog(send);

    type(el, "old");
    await vi.advanceTimersByTimeAsync(300);
    type(el, "new");
    await vi.advanceTimersByTimeAsync(300);
    await el.updateComplete;
    expect(preview(el)).toContain("New");

    first.resolve(PARSED("Old"));
    await vi.advanceTimersByTimeAsync(0);
    await el.updateComplete;
    expect(preview(el)).toContain("New");
    expect(preview(el)).not.toContain("Old");
  });
});

describe("at-add-job-dialog preview line", () => {
  it("is rendered empty before anything is typed, so the dialog keeps its height", async () => {
    const el = await openDialog(vi.fn<Send>());
    const line = el.shadowRoot!.querySelector<HTMLElement>(".preview");
    expect(line).not.toBeNull();
    expect(line!.textContent!.trim()).toBe("");
    expect(line!.getAttribute("aria-live")).toBe("polite");
  });

  it("empties again rather than disappearing when the text is cleared", async () => {
    const el = await openDialog(vi.fn<Send>(() => Promise.resolve(PARSED("New"))));
    type(el, "new");
    await vi.advanceTimersByTimeAsync(300);
    await el.updateComplete;
    expect(preview(el)).toContain("New");

    type(el, "");
    await vi.advanceTimersByTimeAsync(300);
    await el.updateComplete;
    expect(el.shadowRoot!.querySelector(".preview")).not.toBeNull();
    expect(preview(el).trim()).toBe("");
  });
});

describe("at-add-job-dialog submitting", () => {
  it("stays open through Escape while the job is being added, then closes once", async () => {
    const scheduled = deferred<unknown>();
    const send = vi.fn<Send>((msg) => (msg.type === "at/parse" ? Promise.resolve(PARSED("Turn on Porch Light")) : scheduled.promise));
    const el = await openDialog(send);
    const closed = vi.fn();
    el.addEventListener("close-add-job", closed);

    type(el, "turn on the porch light at 11pm");
    await vi.advanceTimersByTimeAsync(300);
    await el.updateComplete;
    $(el, "button.primary").click();
    await el.updateComplete;

    press("Escape");
    $(el, ".backdrop").click();
    await el.updateComplete;
    expect(el.open).toBe(true);
    expect(closed).not.toHaveBeenCalled();
    expect(($(el, ".actions button") as HTMLButtonElement).disabled).toBe(true);

    scheduled.resolve({ job: {} });
    await vi.advanceTimersByTimeAsync(0);
    expect(el.open).toBe(false);
    expect(closed).toHaveBeenCalledTimes(1);
  });

  it("closes on Escape when nothing is in flight", async () => {
    const el = await openDialog(vi.fn<Send>());
    press("Escape");
    await el.updateComplete;
    expect(el.open).toBe(false);
  });
});

describe("at-add-job-dialog focus", () => {
  it("starts in the first field and keeps Tab inside the dialog", async () => {
    const el = await openDialog(vi.fn<Send>());
    const root = el.shadowRoot!;
    expect(root.activeElement).toBe($(el, "#text"));

    const buttons = [...root.querySelectorAll<HTMLButtonElement>(".dialog button")].filter((b) => !b.disabled);
    const first = root.querySelector<HTMLElement>(".dialog button")!;
    const last = buttons[buttons.length - 1];

    last.focus();
    press("Tab");
    expect(root.activeElement).toBe(first);

    press("Tab", true);
    expect(root.activeElement).toBe(last);
  });

  it("gives focus back to what had it when it closes", async () => {
    const opener = document.createElement("button");
    document.body.append(opener);
    opener.focus();
    await openDialog(vi.fn<Send>());
    expect(document.activeElement).not.toBe(opener);

    press("Escape");
    expect(document.activeElement).toBe(opener);
  });
});

async function pickTab(el: AddJobDialog): Promise<PickAction> {
  [...el.shadowRoot!.querySelectorAll<HTMLButtonElement>(".mode")].find((b) => b.textContent === "Pick it")!.click();
  await vi.advanceTimersByTimeAsync(0);
  await el.updateComplete;
  const pick = el.shadowRoot!.querySelector("at-pick-action")!;
  await pick.updateComplete;
  return pick;
}

function serviceValue(pick: PickAction, value: unknown) {
  pick.shadowRoot!.querySelector("ha-service-control")!.dispatchEvent(
    new CustomEvent("value-changed", { detail: { value }, bubbles: true, composed: true }),
  );
}

function addButton(el: AddJobDialog): HTMLButtonElement {
  return $(el, "button.primary") as HTMLButtonElement;
}

describe("at-add-job-dialog Pick it", () => {
  it("enables Add only while an action is chosen and sends it as one step", async () => {
    const send = vi.fn<Send>(async () => ({ job: {} }));
    const el = await openDialog(send);
    const pick = await pickTab(el);
    expect(addButton(el).disabled).toBe(true);

    serviceValue(pick, { action: "light.turn_on", target: { entity_id: ["light.a"] }, data: {} });
    await el.updateComplete;
    expect(addButton(el).disabled).toBe(false);

    serviceValue(pick, {});
    await el.updateComplete;
    expect(addButton(el).disabled).toBe(true);

    serviceValue(pick, { action: "light.turn_on", target: { entity_id: ["light.a"] }, data: { brightness_pct: 80 } });
    await el.updateComplete;
    addButton(el).click();
    await vi.advanceTimersByTimeAsync(0);
    expect(send).toHaveBeenCalledWith({
      type: "at/schedule",
      action: [{ action: "light.turn_on", target: { entity_id: ["light.a"] }, data: { brightness_pct: 80 } }],
      delay_seconds: 900,
    });
    expect(el.open).toBe(false);
  });

  it("keeps the chosen action when switching tabs and back", async () => {
    const el = await openDialog(vi.fn<Send>());
    const pick = await pickTab(el);
    serviceValue(pick, { action: "light.turn_on" });
    await el.updateComplete;
    await pickTab(el);
    expect(el.shadowRoot!.querySelector("at-pick-action")).toBe(pick);
    expect(addButton(el).disabled).toBe(false);
  });

  it("falls back to the plain controls when the elements are missing", async () => {
    loader.defined = false;
    const el = await openDialog(vi.fn<Send>());
    const pick = await pickTab(el);
    expect(pick.ready).toBe(false);
    expect(pick.shadowRoot!.querySelector("at-pick-fallback")).not.toBeNull();
  });

  it("shows a loading status until the loader settles", async () => {
    const first = pending();
    loader.next = () => first.promise;
    const el = await openDialog(vi.fn<Send>());
    $(el, ".mode:nth-child(2)").click();
    await el.updateComplete;
    expect(el.shadowRoot!.querySelector("[role=status]")?.textContent).toBe("Loading…");
    expect(el.shadowRoot!.querySelector("at-pick-action")).toBeNull();
    first.resolve([]);
    const pick = await pickTab(el);
    expect(pick.ready).toBe(true);
  });

  it("keeps the fallback when the elements register later in the same open, and uses them on the next open", async () => {
    loader.defined = false;
    const el = await openDialog(vi.fn<Send>());
    const pick = await pickTab(el);
    expect(pick.ready).toBe(false);

    loader.defined = true;
    el.requestUpdate();
    await el.updateComplete;
    expect(el.shadowRoot!.querySelector("at-pick-action")).toBe(pick);
    expect(pick.ready).toBe(false);

    press("Escape");
    await el.updateComplete;
    el.open = true;
    await el.updateComplete;
    expect((await pickTab(el)).ready).toBe(true);
  });

  it("ignores a loader answer from an earlier open", async () => {
    const first = pending();
    loader.next = () => first.promise;
    const el = await openDialog(vi.fn<Send>());
    press("Escape");
    await el.updateComplete;

    const second = pending();
    loader.next = () => second.promise;
    el.open = true;
    await el.updateComplete;
    first.resolve([]);
    await vi.advanceTimersByTimeAsync(0);
    await el.updateComplete;
    expect(el.shadowRoot!.querySelector("at-pick-action")).toBeNull();

    second.resolve([]);
    expect((await pickTab(el)).ready).toBe(true);
  });
});

describe("at-add-job-dialog Escape inside Home Assistant's popups", () => {
  async function insideControl(el: AddJobDialog): Promise<HTMLElement> {
    const pick = await pickTab(el);
    const inner = document.createElement("input");
    pick.shadowRoot!.querySelector("ha-service-control")!.append(inner);
    return inner;
  }

  function escapeFrom(target: HTMLElement, prevent = false) {
    const e = new KeyboardEvent("keydown", { key: "Escape", bubbles: true, composed: true, cancelable: true });
    if (prevent) target.addEventListener("keydown", (ev) => ev.preventDefault(), { once: true });
    target.dispatchEvent(e);
  }

  it("stays open when the Escape comes from an expanded popup", async () => {
    const el = await openDialog(vi.fn<Send>());
    const inner = await insideControl(el);
    inner.setAttribute("aria-expanded", "true");
    escapeFrom(inner);
    await el.updateComplete;
    expect(el.open).toBe(true);
  });

  it("stays open when a popup already handled the Escape", async () => {
    const el = await openDialog(vi.fn<Send>());
    escapeFrom(await insideControl(el), true);
    await el.updateComplete;
    expect(el.open).toBe(true);
  });

  it("still closes on a plain Escape from inside the form", async () => {
    const el = await openDialog(vi.fn<Send>());
    escapeFrom(await insideControl(el));
    await el.updateComplete;
    expect(el.open).toBe(false);
  });
});

describe("at-add-job-dialog Escape with an open ancestor", () => {
  it("still closes when an element above the dialog reflects open or aria-expanded", async () => {
    const wrapper = document.createElement("div");
    wrapper.setAttribute("open", "");
    wrapper.setAttribute("aria-expanded", "true");
    document.body.append(wrapper);
    const el = await openDialog(vi.fn<Send>());
    wrapper.append(el);
    el.open = false;
    await el.updateComplete;
    el.open = true;
    await el.updateComplete;
    $(el, "#text").dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true, composed: true, cancelable: true }));
    await el.updateComplete;
    expect(el.open).toBe(false);
  });
});

describe("at-add-job-dialog Tab from an HA overlay", () => {
  it("leaves Tab alone when focus is in an overlay outside the dialog", async () => {
    await openDialog(vi.fn<Send>());
    const overlay = document.createElement("input");
    document.body.append(overlay);
    overlay.focus();
    const e = new KeyboardEvent("keydown", { key: "Tab", bubbles: true, composed: true, cancelable: true });
    overlay.dispatchEvent(e);
    expect(e.defaultPrevented).toBe(false);
    expect(document.activeElement).toBe(overlay);
  });

  it("still pulls Tab back into the dialog from the page body", async () => {
    const el = await openDialog(vi.fn<Send>());
    (el.shadowRoot!.activeElement as HTMLElement).blur();
    press("Tab");
    expect(el.shadowRoot!.activeElement).toBe(el.shadowRoot!.querySelector(".dialog button"));
  });
});

describe("at-add-job-dialog Sequence tab", () => {
  const tabs = (el: AddJobDialog) => [...el.shadowRoot!.querySelectorAll(".mode")].map((b) => b.textContent);

  it("shows Sequence only for admins and has no Raw tab", async () => {
    const el = await openDialog(vi.fn<Send>());
    expect(tabs(el)).toEqual(["Type it", "Pick it"]);
    el.isAdmin = true;
    await el.updateComplete;
    expect(tabs(el)).toEqual(["Type it", "Pick it", "Sequence"]);
  });

  async function sequenceTab(el: AddJobDialog) {
    [...el.shadowRoot!.querySelectorAll<HTMLButtonElement>(".mode")].find((b) => b.textContent === "Sequence")!.click();
    await vi.advanceTimersByTimeAsync(0);
    await el.updateComplete;
    const seq = el.shadowRoot!.querySelector("at-sequence-editor")!;
    await seq.updateComplete;
    return seq;
  }

  function steps(seq: Element, value: unknown) {
    seq.shadowRoot!.querySelector("ha-selector")!.dispatchEvent(new CustomEvent("value-changed", { detail: { value }, bubbles: true, composed: true }));
  }

  it("sends the built sequence and keeps it across tab switches without sharing it with Pick it", async () => {
    const send = vi.fn<Send>(async () => ({ job: {} }));
    const el = await openDialog(send);
    el.isAdmin = true;
    await el.updateComplete;
    const seq = await sequenceTab(el);
    expect(addButton(el).disabled).toBe(true);
    steps(seq, [{ action: "light.turn_on" }, { delay: { seconds: 5 } }]);
    await el.updateComplete;
    expect(addButton(el).disabled).toBe(false);

    await pickTab(el);
    expect(addButton(el).disabled).toBe(true);
    expect(await sequenceTab(el)).toBe(seq);
    expect(addButton(el).disabled).toBe(false);

    addButton(el).click();
    await vi.advanceTimersByTimeAsync(0);
    expect(send).toHaveBeenCalledWith({
      type: "at/schedule",
      action: [{ action: "light.turn_on" }, { delay: { seconds: 5 } }],
      delay_seconds: 900,
    });
  });

  it("uses the JSON fallback when the elements are missing", async () => {
    loader.defined = false;
    const el = await openDialog(vi.fn<Send>());
    el.isAdmin = true;
    await el.updateComplete;
    const seq = await sequenceTab(el);
    expect(seq.shadowRoot!.querySelector("#raw")).not.toBeNull();
  });
});
