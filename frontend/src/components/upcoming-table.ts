import { mdiClose, mdiPlay } from "@mdi/js";
import { LitElement, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { formatCountdown, formatWhen } from "../format";
import { sourceLabel } from "../source";
import { upcomingLabel } from "../state";
import type { DataTableColumns, HomeAssistant, Job } from "../types";

interface Row {
  id: string;
  job: Job;
  running: boolean;
  when: string;
  summary: string;
  source: string;
}

@customElement("at-upcoming-table")
export class UpcomingTable extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @property({ attribute: false }) pending: Job[] = [];
  @property({ attribute: false }) running: Job[] = [];
  @property({ type: Number }) now = Date.now();
  @property({ type: Boolean }) isAdmin = false;
  @property({ type: Boolean }) narrow = false;

  private fire(name: string, job: Job, e?: Event) {
    e?.stopPropagation();
    this.dispatchEvent(new CustomEvent(name, { detail: { job }, bubbles: true, composed: true }));
  }

  private when(job: Job): string {
    const due = new Date(job.due);
    const countdown = formatCountdown(due.getTime(), this.now);
    if (countdown) return countdown;
    return formatWhen(due, new Date(this.now), this.hass?.locale?.language ?? this.hass?.language ?? "en", this.hass?.config.time_zone ?? "UTC");
  }

  private actions(row: Row) {
    if (row.running) return nothing;
    const canRun = this.isAdmin || !row.job.raw_action;
    return html`${canRun
        ? html`<ha-icon-button .label=${"Run now"} .path=${mdiPlay} @click=${(e: Event) => this.fire("run-job", row.job, e)}></ha-icon-button>`
        : nothing}
      <ha-icon-button .label=${"Cancel"} .path=${mdiClose} @click=${(e: Event) => this.fire("cancel-job", row.job, e)}></ha-icon-button>`;
  }

  private get columns(): DataTableColumns {
    return {
      when: { title: "When", main: true, minWidth: "120px" },
      summary: { title: "Job", flex: 2 },
      source: { title: "Source" },
      actions: { title: "", type: "icon-button", showNarrow: true, minWidth: "96px", maxWidth: "96px", template: (r: Row) => this.actions(r) },
    };
  }

  private onRowClick(e: CustomEvent<{ id: string }>) {
    const job = [...this.running, ...this.pending].find((j) => j.id === e.detail.id);
    if (job) this.fire("open-job", job);
  }

  protected override render() {
    const row = (job: Job, running: boolean): Row => ({
      id: job.id,
      job,
      running,
      when: running ? "Running…" : this.when(job),
      summary: job.summary,
      source: sourceLabel(job, this.hass),
    });
    const rows = [...this.running.map((j) => row(j, true)), ...this.pending.map((j) => row(j, false))];
    return html`<ha-card .header=${upcomingLabel({ pending: this.pending, running: this.running, history: [] })}>
      <ha-data-table
        .columns=${this.columns}
        .data=${rows}
        .narrow=${this.narrow}
        .noDataText=${"Nothing scheduled."}
        clickable
        auto-height
        @row-click=${this.onRowClick}
      ></ha-data-table>
    </ha-card>`;
  }

  static override styles = css`
    :host {
      display: block;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "at-upcoming-table": UpcomingTable;
  }
}
