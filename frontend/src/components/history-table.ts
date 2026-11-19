import { mdiAlertCircle, mdiCancel, mdiCheckCircle, mdiClockAlert } from "@mdi/js";
import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { live } from "lit/directives/live.js";
import { dateToWallTime, formatWhen, wallTimeToDate } from "../format";
import { HISTORY_LIMIT, visibleHistory } from "../state";
import type { DataTableColumns, HomeAssistant, Job, JobStatus } from "../types";

const ICONS: Record<string, string> = { done: mdiCheckCircle, failed: mdiAlertCircle, missed: mdiClockAlert, cancelled: mdiCancel };
const FILTERS: { value: "all" | JobStatus; label: string }[] = [
  { value: "all", label: "All" },
  { value: "done", label: "Done" },
  { value: "failed", label: "Failed" },
  { value: "missed", label: "Missed" },
  { value: "cancelled", label: "Cancelled" },
];

interface Row {
  id: string;
  job: Job;
  when: string;
  summary: string;
  result: string;
}

@customElement("at-history-table")
export class HistoryTable extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @property({ attribute: false }) history: Job[] = [];
  @property({ type: Number }) now = Date.now();
  @property({ type: Boolean }) narrow = false;

  @state() private filter: "all" | JobStatus = "all";
  @state() private expanded = false;
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

  private selectFilter(e: Event, value: "all" | JobStatus) {
    // The chip toggles itself on click; cancelling the click keeps the selection under our control.
    e.preventDefault();
    this.filter = value;
  }

  private startEditing(job: Job) {
    this.editing = job.id;
    this.value = dateToWallTime(new Date(Date.now() + 3_600_000), this.hass?.config.time_zone ?? "UTC");
  }

  private actions(row: Row) {
    const stop = (e: Event) => e.stopPropagation();
    if (this.editing !== row.id) {
      return html`<ha-button appearance="plain" size="s" @click=${(e: Event) => (stop(e), this.startEditing(row.job))}>Re-schedule</ha-button>`;
    }
    return html`<div class="edit" @click=${stop}>
      <input type="datetime-local" .value=${this.value} @input=${(e: Event) => (this.value = (e.target as HTMLInputElement).value)} />
      <ha-button appearance="plain" size="s" @click=${() => this.submit(row.job)}>Save</ha-button>
      <ha-button appearance="plain" size="s" @click=${() => (this.editing = null)}>Cancel</ha-button>
    </div>`;
  }

  private get columns(): DataTableColumns {
    return {
      status: {
        title: "",
        type: "icon",
        showNarrow: true,
        template: (r: Row) =>
          html`<ha-svg-icon class="status ${r.job.status}" title=${r.job.status} .path=${ICONS[r.job.status] ?? mdiCheckCircle}></ha-svg-icon>`,
      },
      when: { title: "Time", minWidth: "120px" },
      summary: { title: "Job", main: true, flex: 2 },
      result: { title: "Result" },
      actions: { title: "", showNarrow: true, minWidth: this.editing ? "320px" : "130px", template: (r: Row) => this.actions(r) },
    };
  }

  private onRowClick(e: CustomEvent<{ id: string }>) {
    const job = this.history.find((j) => j.id === e.detail.id);
    if (job) this.fire("open-job", { job });
  }

  protected override render() {
    const { rows, matching } = visibleHistory(this.history, this.filter, this.expanded);
    const locale = this.hass?.locale?.language ?? this.hass?.language ?? "en";
    const tz = this.hass?.config.time_zone ?? "UTC";
    const data: Row[] = rows.map((job) => ({
      id: job.id,
      job,
      when: formatWhen(new Date(job.finished_at ?? job.due), new Date(this.now), locale, tz),
      summary: job.summary,
      result: job.result.error ?? "",
    }));
    return html`<ha-card header="History">
      <div class="chips">
        ${FILTERS.map(
          (f) => html`<ha-filter-chip .label=${f.label} .selected=${live(this.filter === f.value)} @click=${(e: Event) => this.selectFilter(e, f.value)}></ha-filter-chip>`,
        )}
      </div>
      <ha-data-table
        .columns=${this.columns}
        .data=${data}
        .narrow=${this.narrow}
        .noDataText=${this.history.length ? "No jobs match this filter." : "No history yet."}
        clickable
        auto-height
        @row-click=${this.onRowClick}
      ></ha-data-table>
      ${!this.expanded && matching > HISTORY_LIMIT
        ? html`<div class="footer"><ha-button appearance="plain" @click=${() => (this.expanded = true)}>Show all (${matching})</ha-button></div>`
        : nothing}
    </ha-card>`;
  }

  static override styles = css`
    :host {
      display: block;
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 0 16px 12px;
    }
    .footer {
      display: flex;
      justify-content: flex-end;
      padding: 8px;
    }
    .edit {
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .status.done {
      color: var(--success-color);
    }
    .status.failed {
      color: var(--error-color);
    }
    .status.missed {
      color: var(--warning-color);
    }
    .status.cancelled {
      color: var(--secondary-text-color);
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "at-history-table": HistoryTable;
  }
}
