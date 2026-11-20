// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from "vitest";
import "../src/components/pick-action";
import type { PickAction } from "../src/components/pick-action";
import type { HomeAssistant } from "../src/types";

class StubServiceControl extends HTMLElement {
  hass?: unknown;
  value?: unknown;
}
customElements.define("ha-service-control", StubServiceControl);

const HASS = {
  config: { time_zone: "UTC" },
  language: "en",
  states: { "light.a": { attributes: { friendly_name: "A" } } },
} as unknown as HomeAssistant;

async function mount(ready: boolean): Promise<{ el: PickAction; changed: ReturnType<typeof vi.fn> }> {
  const el = document.createElement("at-pick-action");
  el.hass = HASS;
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

describe("at-pick-action with Home Assistant's form", () => {
  it("renders ha-service-control and maps its value to one step", async () => {
    const { el, changed } = await mount(true);
    const control = el.shadowRoot!.querySelector("ha-service-control") as StubServiceControl;
    expect(control).not.toBeNull();
    expect(control.hass).toBe(HASS);
    expect(control.hasAttribute("narrow")).toBe(true);

    emit(control, { action: "light.turn_on", target: { entity_id: ["light.a"] }, data: {} });
    expect(changed).toHaveBeenLastCalledWith([{ action: "light.turn_on", target: { entity_id: ["light.a"] } }]);
    await el.updateComplete;
    expect(control.value).toEqual({ action: "light.turn_on", target: { entity_id: ["light.a"] }, data: {} });

    emit(control, {});
    expect(changed).toHaveBeenLastCalledWith(undefined);
  });

  it("does not let the action-changed event bubble", async () => {
    const { el } = await mount(true);
    const outer = vi.fn();
    document.body.addEventListener("action-changed", outer);
    emit(el.shadowRoot!.querySelector("ha-service-control")!, { action: "light.turn_on" });
    expect(outer).not.toHaveBeenCalled();
  });
});

describe("at-pick-action fallback", () => {
  it("renders the plain controls and builds the picked shape", async () => {
    const { el, changed } = await mount(false);
    expect(el.shadowRoot!.querySelector("ha-service-control")).toBeNull();
    const fallback = el.shadowRoot!.querySelector("at-pick-fallback")!;
    expect(fallback).not.toBeNull();
    await (fallback as unknown as { updateComplete: Promise<unknown> }).updateComplete;

    const entity = fallback.shadowRoot!.querySelector<HTMLSelectElement>("#entity")!;
    entity.value = "light.a";
    entity.dispatchEvent(new Event("change"));
    await (fallback as unknown as { updateComplete: Promise<unknown> }).updateComplete;
    expect(changed).toHaveBeenLastCalledWith([{ action: "homeassistant.turn_on", target: { entity_id: ["light.a"] } }]);

    const op = fallback.shadowRoot!.querySelector<HTMLSelectElement>("#op")!;
    op.value = "toggle";
    op.dispatchEvent(new Event("change"));
    await (fallback as unknown as { updateComplete: Promise<unknown> }).updateComplete;
    expect(changed).toHaveBeenLastCalledWith(undefined);
  });
});
