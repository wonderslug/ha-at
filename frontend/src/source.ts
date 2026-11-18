import type { HomeAssistant, Job } from "./types";

/** Human label for where a job came from. */
export function sourceLabel(job: Job, hass: HomeAssistant | undefined): string {
  const { via, device_id, user_id } = job.source;
  if (via === "voice" || via === "llm") {
    const device = device_id ? hass?.devices?.[device_id] : undefined;
    return `🎙 ${device?.name_by_user ?? device?.name ?? "Voice"}`;
  }
  if (via === "panel" || via === "todo") {
    const name = user_id && hass?.user?.id === user_id ? hass.user.name : "User";
    return `🖱 ${name}`;
  }
  return "⚙ Automation";
}

function scalar(v: unknown): string {
  return typeof v === "string" && /^[\w./:-]+$/.test(v) ? v : JSON.stringify(v);
}

/** Minimal YAML dump for the stored action (plain data only). */
export function toYaml(value: unknown, indent = 0): string {
  const pad = "  ".repeat(indent);
  if (Array.isArray(value)) {
    if (value.length === 0) return `${pad}[]`;
    return value
      .map((item) => {
        if (item !== null && typeof item === "object") {
          const inner = toYaml(item, indent + 1).replace(/^\s+/, "");
          return `${pad}- ${inner}`;
        }
        return `${pad}- ${scalar(item)}`;
      })
      .join("\n");
  }
  if (value !== null && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);
    if (entries.length === 0) return `${pad}{}`;
    return entries
      .map(([k, v]) => {
        if (v !== null && typeof v === "object" && (Array.isArray(v) ? v.length : Object.keys(v).length)) {
          return `${pad}${k}:\n${toYaml(v, indent + 1)}`;
        }
        return `${pad}${k}: ${v !== null && typeof v === "object" ? toYaml(v) : scalar(v)}`;
      })
      .join("\n");
  }
  return `${pad}${scalar(value)}`;
}
