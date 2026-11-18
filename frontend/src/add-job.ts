/** Pure helpers for the Add job dialog. Shapes must match the backend's `validate_picked_action`. */

export type Verb = "turn_on" | "turn_off" | "toggle";

export type PickedInput =
  | { targetEntityIds: string[]; verb: Verb }
  | { script: string; variables?: Record<string, unknown> }
  | { automation: string };

export function buildPickedAction(p: PickedInput): Record<string, unknown>[] {
  if ("verb" in p) {
    return [{ action: `homeassistant.${p.verb}`, target: { entity_id: [...p.targetEntityIds] } }];
  }
  if ("script" in p) {
    const step: Record<string, unknown> = { action: "script.turn_on", target: { entity_id: p.script } };
    if (p.variables && Object.keys(p.variables).length > 0) {
      step.data = { variables: p.variables };
    }
    return [step];
  }
  return [{ action: "automation.trigger", target: { entity_id: p.automation } }];
}

export function quickDue(chip: "+15m" | "+1h", _now: Date): { delay_seconds: number } {
  return { delay_seconds: chip === "+15m" ? 900 : 3600 };
}

export type Parsed<T> = { ok: true; value: T } | { ok: false; error: string };

/** Blank is an empty object; anything else must be a JSON object. */
export function parseJsonObject(text: string): Parsed<Record<string, unknown>> {
  if (!text.trim()) return { ok: true, value: {} };
  try {
    const value: unknown = JSON.parse(text);
    if (value && typeof value === "object" && !Array.isArray(value)) {
      return { ok: true, value: value as Record<string, unknown> };
    }
    return { ok: false, error: "Must be a JSON object, like {\"key\": \"value\"}" };
  } catch {
    return { ok: false, error: "Invalid JSON" };
  }
}

/** A JSON list of action objects, for the admin-only raw mode. */
export function parseRawAction(text: string): Parsed<Record<string, unknown>[]> {
  try {
    const value: unknown = JSON.parse(text);
    if (
      Array.isArray(value) &&
      value.length > 0 &&
      value.every((s) => s && typeof s === "object" && !Array.isArray(s))
    ) {
      return { ok: true, value: value as Record<string, unknown>[] };
    }
    return { ok: false, error: "Must be a non-empty JSON list of action objects" };
  } catch {
    return { ok: false, error: "Invalid JSON" };
  }
}

/** True when `due` is a valid date strictly after `now`. */
export function isFuture(due: Date, now: Date): boolean {
  return !Number.isNaN(due.getTime()) && due.getTime() > now.getTime();
}
