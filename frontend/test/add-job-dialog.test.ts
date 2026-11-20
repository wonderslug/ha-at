// @vitest-environment happy-dom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import "../src/components/add-job-dialog";
import type { AddJobDialog } from "../src/components/add-job-dialog";
import type { HomeAssistant } from "../src/types";

type Send = (msg: { type: string; text?: string }) => Promise<unknown>;

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => (resolve = r));
  return { promise, resolve };
}

const PARSED = (summary: string) => ({ ok: true, due: "2026-11-20T12:00:00Z", summary });

async function openDialog(send: Send): Promise<AddJobDialog> {
  const el = document.createElement("at-add-job-dialog");
  el.hass = { config: { time_zone: "UTC" }, language: "en", states: {}, connection: { sendMessagePromise: send } } as unknown as HomeAssistant;
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
