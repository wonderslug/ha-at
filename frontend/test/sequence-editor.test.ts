// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from "vitest";
import "../src/components/sequence-editor";
import type { SequenceEditor } from "../src/components/sequence-editor";
import { enHass, enLocalize } from "./en-localize";

class StubSelector extends HTMLElement {
  hass?: unknown;
  selector?: unknown;
  value?: unknown;
}
customElements.define("ha-selector", StubSelector);

const HASS = enHass();

async function mount(ready: boolean): Promise<{ el: SequenceEditor; changed: ReturnType<typeof vi.fn> }> {
  const el = document.createElement("at-sequence-editor");
  el.hass = HASS;
  el.localize = enLocalize;
  el.ready = ready;
  const changed = vi.fn();
  el.addEventListener("action-changed", (e) => changed((e as CustomEvent).detail.action));
  document.body.append(el);
  await el.updateComplete;
  return { el, changed };
}

function emit(control: Element, value: unknown) {
  control.dispatchEvent(new CustomEvent("value-changed", { detail: { value }, bubbles: true, composed: true }));
}

afterEach(() => document.body.replaceChildren());

describe("at-sequence-editor with Home Assistant's editor", () => {
  it("renders ha-selector for an action list and reports the steps", async () => {
    const { el, changed } = await mount(true);
    const sel = el.shadowRoot!.querySelector("ha-selector") as StubSelector;
    expect(sel.selector).toEqual({ action: {} });
    expect(sel.hass).toBe(HASS);
    const steps = [{ action: "light.turn_on" }, { delay: { seconds: 5 } }];
    emit(sel, steps);
    expect(changed).toHaveBeenLastCalledWith(steps);
    emit(sel, []);
    expect(changed).toHaveBeenLastCalledWith(undefined);
    emit(sel, "nope");
    expect(changed).toHaveBeenLastCalledWith(undefined);
  });

  it("does not let value-changed or action-changed escape", async () => {
    const { el } = await mount(true);
    const outer = vi.fn();
    document.body.addEventListener("value-changed", outer);
    document.body.addEventListener("action-changed", outer);
    emit(el.shadowRoot!.querySelector("ha-selector")!, [{ action: "a.b" }]);
    expect(outer).not.toHaveBeenCalled();
  });
});

describe("at-sequence-editor fallback", () => {
  it("shows a JSON textarea and reports parsed lists", async () => {
    const { el, changed } = await mount(false);
    expect(el.shadowRoot!.querySelector("ha-selector")).toBeNull();
    const ta = el.shadowRoot!.querySelector<HTMLTextAreaElement>("#raw")!;
    ta.value = '[{"action": "light.turn_on"}]';
    ta.dispatchEvent(new Event("input"));
    await el.updateComplete;
    expect(changed).toHaveBeenLastCalledWith([{ action: "light.turn_on" }]);
    expect(el.shadowRoot!.querySelector(".inline-error")).toBeNull();

    ta.value = "{nope";
    ta.dispatchEvent(new Event("input"));
    await el.updateComplete;
    expect(changed).toHaveBeenLastCalledWith(undefined);
    expect(el.shadowRoot!.querySelector(".inline-error")?.textContent).toBe("Invalid JSON");
  });
});
