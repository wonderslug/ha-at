import type { HomeAssistant } from "./types";

export type Localize = (key: string, values?: Record<string, string | number>) => string;

const PREFIX = "component.at.config_panel.";

/** Localizes a key under `config_panel`; a missing translation falls back to the key itself. */
export function makeLocalize(hass: HomeAssistant): Localize {
  return (key, values) => hass.localize(`${PREFIX}${key}`, values) || key;
}
