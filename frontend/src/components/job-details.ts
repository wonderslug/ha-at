import { LitElement, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { sourceLabel, toYaml } from "../source";
import type { HomeAssistant, Job } from "../types";

@customElement("at-job-details")
export class JobDetails extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @property({ attribute: false }) job?: Job;

  private close() {
    this.dispatchEvent(new CustomEvent("close-details", { bubbles: true, composed: true }));
  }

  protected override render() {
    const job = this.job;
    if (!job) return nothing;
    const tz = this.hass?.config.time_zone ?? "UTC";
    const locale = this.hass?.locale?.language ?? this.hass?.language ?? "en";
    const created = new Intl.DateTimeFormat(locale, { timeZone: tz, dateStyle: "medium", timeStyle: "medium" }).format(new Date(job.created_at));
    const what = job.intent
      ? `${job.intent.type}\n${toYaml(job.intent.slots)}`
      : toYaml(job.action ?? []);
    return html`<div class="backdrop" @click=${() => this.close()}>
      <div class="card" role="dialog" aria-label="Job details" @click=${(e: Event) => e.stopPropagation()}>
        <h2>${job.summary}</h2>
        <dl>
          <dt>${job.intent ? "Intent" : "Action"}</dt>
          <dd><pre>${what}</pre></dd>
          <dt>Created by</dt>
          <dd>${sourceLabel(job, this.hass)}</dd>
          <dt>Created</dt>
          <dd>${created}</dd>
          <dt>ID</dt>
          <dd><code>${job.id}</code></dd>
        </dl>
        <button @click=${() => this.close()}>Close</button>
      </div>
    </div>`;
  }

  static override styles = css`
    .backdrop { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 10; }
    .card { background: var(--card-background-color); color: var(--primary-text-color); border-radius: 8px; padding: 16px 24px; max-width: 560px; width: calc(100% - 32px); max-height: 80vh; overflow: auto; }
    h2 { margin-top: 0; font-weight: 400; }
    dt { color: var(--secondary-text-color); font-size: 12px; margin-top: 12px; }
    dd { margin: 2px 0 0; }
    pre { margin: 0; white-space: pre-wrap; font-family: var(--code-font-family, monospace); }
    button { font: inherit; margin-top: 16px; color: var(--primary-color); background: none; border: none; cursor: pointer; }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "at-job-details": JobDetails;
  }
}
