import type { AtInfo, HomeAssistant, Job, ParseResult, SchedulePayload, SubscribeEvent } from "./types";

/** Subscribe to the snapshot and changes; resolves to the unsubscribe function. */
export function subscribeJobs(hass: HomeAssistant, cb: (event: SubscribeEvent) => void): Promise<() => Promise<void>> {
  return hass.connection.subscribeMessage<SubscribeEvent>(cb, { type: "at/subscribe" });
}

export function parse(hass: HomeAssistant, text: string): Promise<ParseResult> {
  return hass.connection.sendMessagePromise<ParseResult>({ type: "at/parse", text });
}

export function schedule(hass: HomeAssistant, payload: SchedulePayload): Promise<{ job: Job }> {
  return hass.connection.sendMessagePromise({ type: "at/schedule", ...payload });
}

export function cancel(hass: HomeAssistant, ids: string[]): Promise<{ cancelled: string[] }> {
  return hass.connection.sendMessagePromise({ type: "at/cancel", job_ids: ids });
}

export function runNow(hass: HomeAssistant, id: string): Promise<{ job: Job }> {
  return hass.connection.sendMessagePromise({ type: "at/run_now", job_id: id });
}

/** `due` is an ISO string. */
export function reschedule(hass: HomeAssistant, id: string, due: string): Promise<{ job: Job }> {
  return hass.connection.sendMessagePromise({ type: "at/reschedule", job_id: id, due });
}

export function clearHistory(hass: HomeAssistant): Promise<{ removed: number }> {
  return hass.connection.sendMessagePromise({ type: "at/clear_history" });
}

export function info(hass: HomeAssistant): Promise<AtInfo> {
  return hass.connection.sendMessagePromise({ type: "at/info" });
}
