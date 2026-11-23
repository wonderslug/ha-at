import { config_panel as english } from "../../custom_components/at/translations/en.json";
import type { HomeAssistant } from "./types";

export type Localize = (key: string, values?: Record<string, string | number>) => string;

const PREFIX = "component.at.config_panel.";

function bundled(key: string, values?: Record<string, string | number>): string {
  let node: unknown = english;
  for (const part of key.split(".")) {
    if (typeof node !== "object" || node === null) return "";
    node = (node as Record<string, unknown>)[part];
  }
  if (typeof node !== "string") return "";
  return node.replace(/\{(\w+)\}/g, (match, name: string) => (values && name in values ? String(values[name]) : match));
}

/** Localizes a key under `config_panel`; without a translation it shows the bundled English, then the key. */
export function makeLocalize(hass: HomeAssistant): Localize {
  return (key, values) => hass.localize(`${PREFIX}${key}`, values) || bundled(key, values) || key;
}
