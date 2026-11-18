import { LitElement, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { dateToWallTime, formatWhen, wallTimeToDate } from "../format";
import type { HomeAssistant, Job, JobStatus } from "../types";

const ICONS: Record<string, string> = { done: "✓", failed: "✗", missed: "⚠", cancelled: "⊘" };
const FILTERS: ("all" | JobStatus)[] = ["all", "done", "failed", "missed", "cancelled"];

@customElement("at-history-table")
export class HistoryTable extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @property({ attribute: false }) history: Job[] = [];
  @property({ type: Number }) now = Date.now();

  @state() private filter: "all" | JobStatus = "all";
  @state() private editing: string | null = null;
  @state() private value = "";

  private fire(name: string, detail: unknown) {
    this.dispatchEvent(new CustomEvent(name, { detail, bubbles: true, composed: true }));
  }

  private submit(job: Job) {
    if (!this.value) return;
    const due = wallTimeToDate(this.value, this.hass?.config.time_zone ?? "UTC");
    if (Number.isNaN(due.getTime())) return;
    this.fire("reschedule-job", { job, due: due.toISOString() });
    this.editing = null;
    this.value = "";
  }

  private row(job: Job) {
    const when = formatWhen(
      new Date(job.finished_at ?? job.due),
      new Date(this.now),
      this.hass?.locale?.language ?? this.hass?.language ?? "en",
      this.hass?.config.time_zone ?? "UTC",
    );
    return html`<tr @click=${() => this.fire("open-job", { job })}>
      <td class="status ${job.status}" title=${job.status}>${ICONS[job.status] ?? job.status}</td>
      <td class="nowrap">${when}</td>
      <td>${job.summary}</td>
      <td class="result">${job.result.error ?? ""}</td>
      <td class="actions" @click=${(e: Event) => e.stopPropagation()}>
        ${this.editing === job.id
          ? html`<input type="datetime-local" .value=${this.value} @input=${(e: Event) => (this.value = (e.target as HTMLInputElement).value)} />
              <button @click=${() => this.submit(job)}>Save</button>
              <button @click=${() => (this.editing = null)}>Cancel</button>`
          : html`<button @click=${() => { this.editing = job.id; this.value = dateToWallTime(new Date(Date.now() + 3_600_000), this.hass?.config.time_zone ?? "UTC"); }}>Re-schedule</button>`}
      </td>
    </tr>`;
  }

  protected override render() {
    const rows = this.filter === "all" ? this.history : this.history.filter((j) => j.status === this.filter);
    return html`
      <div class="chips">
        ${FILTERS.map(
          (f) => html`<button class="chip ${this.filter === f ? "on" : ""}" @click=${() => (this.filter = f)}>${f === "all" ? "All" : `${ICONS[f]} ${f}`}</button>`,
        )}
      </div>
      ${rows.length
        ? html`<table>
            <thead><tr><th></th><th>Time</th><th>Job</th><th>Result</th><th></th></tr></thead>
            <tbody>${rows.map((j) => this.row(j))}</tbody>
          </table>`
        : html`<p class="empty">${this.history.length ? "No jobs match this filter." : "No history yet."}</p>`}
    `;
  }

  static override styles = css`
    .chips { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
    .chip { font: inherit; color: var(--primary-text-color); background: none; border: 1px solid var(--divider-color); border-radius: 16px; padding: 4px 12px; cursor: pointer; }
    .chip.on { background: var(--primary-color); color: var(--text-primary-color, #fff); border-color: var(--primary-color); }
    table { width: 100%; border-collapse: collapse; background: var(--card-background-color); border-radius: 8px; }
    th { text-align: left; padding: 8px 12px; color: var(--secondary-text-color); font-weight: 500; }
    td { padding: 10px 12px; border-top: 1px solid var(--divider-color); }
    tr { cursor: pointer; }
    .nowrap { white-space: nowrap; }
    .status { font-size: 18px; width: 24px; }
    .status.done { color: var(--success-color, #43a047); }
    .status.failed { color: var(--error-color, #db4437); }
    .status.missed { color: var(--warning-color, #ffa600); }
    .status.cancelled { color: var(--secondary-text-color); }
    .result { color: var(--secondary-text-color); }
    .actions { text-align: right; white-space: nowrap; }
    .actions button { font: inherit; color: var(--primary-color); background: none; border: none; cursor: pointer; padding: 4px 8px; }
    .empty { color: var(--secondary-text-color); text-align: center; padding: 32px; }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "at-history-table": HistoryTable;
  }
}
