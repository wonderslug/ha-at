import type { HomeAssistant, Job } from "./types";

const WHERE: Record<string, string> = {
  voice: "Assist",
  llm: "Assist",
  panel: "Add job",
  reschedule: "Reschedule",
  todo: "To-do list",
};

const CANCEL_WHERE: Record<string, string> = {
  voice: "from Assist",
  llm: "from Assist",
  panel: "in the panel",
  todo: "from the to-do list",
  service: "by an action",
};

const isAssist = (via: string | null | undefined) => via === "voice" || via === "llm";

/** A user's name as Activity shows it: their person's name, else the signed-in user's own name. */
function userName(userId: string | null | undefined, hass: HomeAssistant | undefined): string | undefined {
  if (!userId) return undefined;
  const person = Object.entries(hass?.states ?? {}).find(([id, s]) => id.startsWith("person.") && s.attributes.user_id === userId);
  if (person) return person[1].attributes.friendly_name ?? person[0];
  return hass?.user?.id === userId ? hass.user.name : undefined;
}

function deviceName(deviceId: string | null | undefined, hass: HomeAssistant | undefined): string | undefined {
  const device = deviceId ? hass?.devices?.[deviceId] : undefined;
  return device?.name_by_user ?? device?.name ?? undefined;
}

function originName(entityId: string, hass: HomeAssistant | undefined): string {
  return hass?.states?.[entityId]?.attributes.friendly_name ?? entityId;
}

const capitalised = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

/** Where a job came from, who made it and through what, as "Assist · Kitchen satellite · Brian". */
export function sourceLabel(job: Job, hass: HomeAssistant | undefined): string {
  const { via, device_id, user_id, origin } = job.source;
  const where = origin ? [capitalised(origin.split(".")[0]), originName(origin, hass)] : [WHERE[via] ?? "Action"];
  const device = isAssist(via) ? deviceName(device_id, hass) : undefined;
  return [...where, device, userName(user_id, hass)].filter(Boolean).join(" · ");
}

function cancelDetail(result: Job["result"], hass: HomeAssistant | undefined): string {
  const origin = result.cancelled_origin;
  const device = isAssist(result.cancelled_by) ? deviceName(result.cancelled_device_id, hass) : undefined;
  const where = origin
    ? `by ${origin.split(".")[0]} ${originName(origin, hass)}`
    : [CANCEL_WHERE[result.cancelled_by ?? ""], device].filter(Boolean).join(" · ");
  const who = userName(result.cancelled_user_id, hass);
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
