/** Types mirroring the Python `Job.to_dict()` and the websocket API of the `at` integration. */

export type JobStatus = "pending" | "running" | "done" | "failed" | "cancelled" | "missed";
export type JobKind = "intent" | "action";

export interface JobIntent {
  type: string;
  slots: Record<string, unknown>;
  language: string;
  device_id: string | null;
  satellite_id: string | null;
}

export interface Job {
  id: string;
  kind: JobKind;
  status: JobStatus;
  /** ISO 8601 UTC. */
  due: string;
  created_at: string;
  finished_at: string | null;
  summary: string;
  original_text: string | null;
  intent: JobIntent | null;
  action: Record<string, unknown>[] | null;
  raw_action: boolean;
  targets: {
    entity_ids: string[];
    area_ids: string[];
    floor_ids: string[];
    names: string[];
  };
  source: {
    via: string;
    user_id: string | null;
    device_id: string | null;
    agent_id: string | null;
    /** Entity id of the automation or script that scheduled the job. */
    origin?: string | null;
  };
  result: {
    error: string | null;
    /** The channel the cancel came through: panel, voice, llm, todo or service. */
    cancelled_by: string | null;
    cancelled_user_id?: string | null;
    /** Entity id of the automation or script that issued the cancel. */
    cancelled_origin?: string | null;
    /** The satellite or other device an Assist cancel came from. */
    cancelled_device_id?: string | null;
  };
}

export interface Snapshot {
  pending: Job[];
  history: Job[];
  running: Job[];
}

export type JobChangeKind = "added" | "updated" | "removed";

export type SubscribeEvent =
  | { snapshot: Snapshot }
  | { change: { kind: JobChangeKind; job: Job } }
  | { stopped: true };

export type ParseResult = { ok: true; summary: string; due: string } | { ok: false; message: string };

export interface SchedulePayload {
  /** Natural-language command; or give `action` plus exactly one of `due` and `delay_seconds`. */
  text?: string;
  action?: Record<string, unknown>[];
  due?: string;
  delay_seconds?: number;
}

export interface AtInfo {
  is_admin: boolean;
  panel_admin_only: boolean;
  language_supported: boolean;
}

/** The slice of Home Assistant's `hass` object the panel uses. */
export interface HomeAssistant {
  connection: {
    sendMessagePromise<T>(message: Record<string, unknown>): Promise<T>;
    subscribeMessage<T>(
      callback: (event: T) => void,
      subscribeMessage: Record<string, unknown>,
    ): Promise<() => Promise<void>>;
  };
  language: string;
  localize(key: string, values?: Record<string, string | number>): string;
  loadBackendTranslation(category: string, integration?: string): Promise<unknown>;
  locale?: { language: string };
  config: { time_zone: string };
  themes?: { darkMode?: boolean };
  user?: { id: string; name: string };
  states?: Record<string, { state: string; attributes: { friendly_name?: string; user_id?: string } }>;
  devices?: Record<string, { name?: string | null; name_by_user?: string | null }>;
}

export interface PanelInfo {
  config?: Record<string, unknown>;
}

/** Column definitions for HA's `ha-data-table`, keyed by row field. */
export type DataTableColumns = Record<string, Record<string, unknown>>;
