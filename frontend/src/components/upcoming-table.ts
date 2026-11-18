import { LitElement, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { formatCountdown, formatWhen } from "../format";
import { sourceLabel } from "../source";
import type { HomeAssistant, Job } from "../types";

@customElement("at-upcoming-table")
export class UpcomingTable extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @property({ attribute: false }) pending: Job[] = [];
  @property({ attribute: false }) running: Job[] = [];
  @property({ type: Number }) now = Date.now();
  @property({ type: Boolean }) isAdmin = false;

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

  private row(job: Job, running: boolean) {
    const canRun = !running && (this.isAdmin || !job.raw_action);
    return html`<tr @click=${() => this.fire("open-job", job)}>
      <td class="when">${running ? "Running…" : this.when(job)}</td>
      <td>${job.summary}</td>
      <td>${sourceLabel(job, this.hass)}</td>
      <td class="actions">
        ${running
          ? nothing
          : html`${canRun
              ? html`<button title="Run now" aria-label="Run now" @click=${(e: Event) => this.fire("run-job", job, e)}>▶</button>`
              : nothing}
            <button title="Cancel" aria-label="Cancel" @click=${(e: Event) => this.fire("cancel-job", job, e)}>✕</button>`}
      </td>
    </tr>`;
  }

  protected override render() {
    if (!this.pending.length && !this.running.length) {
      return html`<p class="empty">Nothing scheduled.</p>`;
    }
    return html`<table>
      <thead><tr><th>When</th><th>Job</th><th>Source</th><th></th></tr></thead>
      <tbody>
        ${this.running.map((j) => this.row(j, true))} ${this.pending.map((j) => this.row(j, false))}
      </tbody>
    </table>`;
  }

  static override styles = css`
    table { width: 100%; border-collapse: collapse; background: var(--card-background-color); border-radius: 8px; }
    th { text-align: left; padding: 8px 12px; color: var(--secondary-text-color); font-weight: 500; }
    td { padding: 10px 12px; border-top: 1px solid var(--divider-color); }
    tr { cursor: pointer; }
    tbody tr:hover { background: var(--secondary-background-color); }
    .when { font-variant-numeric: tabular-nums; white-space: nowrap; }
    .actions { text-align: right; white-space: nowrap; }
    button { font: inherit; color: var(--primary-text-color); background: none; border: none; cursor: pointer; padding: 4px 8px; }
    .empty { color: var(--secondary-text-color); text-align: center; padding: 32px; }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "at-upcoming-table": UpcomingTable;
  }
}
