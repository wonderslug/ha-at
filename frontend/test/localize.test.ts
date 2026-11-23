// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from "vitest";
import "../src/at-panel";
import type { AtPanel } from "../src/at-panel";
import { makeLocalize } from "../src/localize";
import type { HomeAssistant } from "../src/types";
import { enHass } from "./en-localize";

afterEach(() => {
  document.body.replaceChildren();
});

describe("makeLocalize", () => {
  it("prefixes the key", () => {
    const localize = vi.fn(() => "x");
    makeLocalize(enHass({ localize }))("upcoming.title");
    expect(localize).toHaveBeenCalledWith("component.at.config_panel.upcoming.title", undefined);
  });

  it("falls back to bundled English before the translations load", () => {
    const localize = makeLocalize(enHass({ localize: () => "" }));
    expect(localize("panel.add_job")).toBe("Add job");
    expect(localize("panel.missing_elements", { elements: "a, b" })).toBe("Missing: a, b");
  });

  it("falls back to the key when English has none either", () => {
    expect(makeLocalize(enHass({ localize: () => "" }))("no.such.key")).toBe("no.such.key");
  });

  it("substitutes placeholders", () => {
    expect(makeLocalize(enHass())("panel.missing_elements", { elements: "a, b" })).toBe("Missing: a, b");
  });
});

async function mount(hass: HomeAssistant): Promise<AtPanel> {
  const el = document.createElement("at-panel") as AtPanel;
  el.hass = hass;
  document.body.append(el);
  await el.updateComplete;
  return el;
}

describe("panel translations", () => {
  it("loads config_panel on start", async () => {
    const load = vi.fn(() => Promise.resolve({}));
    await mount(enHass({ loadBackendTranslation: load }));
    expect(load).toHaveBeenCalledTimes(1);
    expect(load).toHaveBeenCalledWith("config_panel", "at");
  });

  it("reloads translations when hass.language changes", async () => {
    const load = vi.fn(() => Promise.resolve({}));
    const el = await mount(enHass({ loadBackendTranslation: load }));
    el.hass = enHass({ language: "de", loadBackendTranslation: load });
    await el.updateComplete;
    expect(load).toHaveBeenCalledTimes(2);
    el.hass = enHass({ language: "de", loadBackendTranslation: load });
    await el.updateComplete;
    expect(load).toHaveBeenCalledTimes(2);
  });

  it("keeps rendering when loading fails", async () => {
    const load = vi.fn(() => Promise.reject(new Error("offline")));
    const el = await mount(enHass({ loadBackendTranslation: load }));
    await Promise.resolve();
    await el.updateComplete;
    expect(el.isConnected).toBe(true);
  });
});
