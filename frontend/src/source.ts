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

const CANCEL_WHERE: Record<string, string> = {
  panel: "from the panel",
  voice: "with voice",
  llm: "with voice",
  todo: "from the to-do list",
  service: "by an action",
};

/** A user's name as Activity shows it: their person's name, else the signed-in user's own name. */
function userName(userId: string, hass: HomeAssistant | undefined): string | undefined {
  const person = Object.entries(hass?.states ?? {}).find(([id, s]) => id.startsWith("person.") && s.attributes.user_id === userId);
  if (person) return person[1].attributes.friendly_name ?? person[0];
  return hass?.user?.id === userId ? hass.user.name : undefined;
}

function cancelDetail(result: Job["result"], hass: HomeAssistant | undefined): string {
  const origin = result.cancelled_origin;
  const where = origin
    ? `by ${origin.split(".")[0]} ${hass?.states?.[origin]?.attributes.friendly_name ?? origin}`
    : CANCEL_WHERE[result.cancelled_by ?? ""];
  const who = result.cancelled_user_id ? userName(result.cancelled_user_id, hass) : undefined;
  return ["Cancelled", where, who && `by ${who}`].filter(Boolean).join(" ");
}

/** The History "Details" text: why a job failed, was missed, or who cancelled it and from where. */
export function historyDetail(job: Job, hass: HomeAssistant | undefined): string {
  switch (job.status) {
    case "failed":
      return job.result.error ?? "";
    case "missed":
      return "Home Assistant was off when it was due";
    case "cancelled":
      return cancelDetail(job.result, hass);
    default:
      return "";
  }
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
