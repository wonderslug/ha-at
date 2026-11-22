import en from "../../custom_components/at/translations/en.json";
import type { HomeAssistant } from "../src/types";

const PREFIX = "component.at.config_panel.";

function lookup(path: string): string {
  let node: unknown = (en as { config_panel: unknown }).config_panel;
  for (const part of path.split(".")) {
    if (typeof node !== "object" || node === null) return "";
    node = (node as Record<string, unknown>)[part];
  }
  return typeof node === "string" ? node : "";
}

/** A `hass` whose `localize` answers from the real English `config_panel` strings. */
export function enHass(partial: Partial<HomeAssistant> = {}): HomeAssistant {
  return {
    connection: {
      sendMessagePromise: () => Promise.resolve({}),
      subscribeMessage: () => Promise.resolve(() => Promise.resolve()),
    },
    language: "en",
    config: { time_zone: "UTC" },
    localize: (key, values) => {
      if (!key.startsWith(PREFIX)) return "";
      const text = lookup(key.slice(PREFIX.length));
      return text.replace(/\{(\w+)\}/g, (match, name: string) => (values && name in values ? String(values[name]) : match));
    },
    loadBackendTranslation: () => Promise.resolve({}),
    ...partial,
  } as HomeAssistant;
}
