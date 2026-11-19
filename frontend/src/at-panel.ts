import { mdiDotsVertical, mdiPlus } from "@mdi/js";
import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import * as api from "./api";
import "./components/add-job-dialog";
import "./components/history-table";
import "./components/job-details";
import "./components/upcoming-table";
import { loadHaElements } from "./ha-elements";
import { nextRetryDelay } from "./reconnect";
import { applyChange, normalize, type PanelState } from "./state";
import type { AtInfo, HomeAssistant, Job, PanelInfo, SubscribeEvent } from "./types";

const DEFAULT_TITLE = "Scheduled Jobs";

@customElement("at-panel")
export class AtPanel extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @property({ type: Boolean }) narrow = false;
  @property({ attribute: false }) panel?: PanelInfo;
  @property({ attribute: false }) route?: unknown;

  @state() private missing?: string[];
  @state() private data: PanelState = { pending: [], running: [], history: [] };
  @state() private now = Date.now();
  @state() private reconnecting = true;
  @state() private error = "";
  @state() private confirmCancelAll = false;
  @state() private details?: Job;
  @state() private atInfo?: AtInfo;
  @state() private addOpen = false;

  private tick?: number;
  private unsub?: () => Promise<void>;
  private retryTimer?: number;
  private attempt = 0;
  private subscribed = false;
  private gone = false;
  private generation = 0;

  override connectedCallback() {
    super.connectedCallback();
    this.gone = false;
    this.generation++;
    window.clearInterval(this.tick);
    this.tick = window.setInterval(() => (this.now = Date.now()), 1000);
    if (this.hass) void this.start();
  }

  override disconnectedCallback() {
    super.disconnectedCallback();
    this.gone = true;
    this.generation++;
    window.clearInterval(this.tick);
    window.clearTimeout(this.retryTimer);
    this.subscribed = false;
    void this.unsub?.().catch(() => undefined);
    this.unsub = undefined;
  }

  protected override updated(changed: Map<string, unknown>) {
    if (changed.has("hass") && this.hass && !this.subscribed && !this.gone) {
      void this.start();
    }
  }

  private async start() {
    if (!this.hass || this.subscribed) return;
    this.subscribed = true;
    api.info(this.hass).then((i) => (this.atInfo = i), () => undefined);
    void loadHaElements().then((missing) => (this.missing = missing));
    await this.subscribe();
  }

  private async subscribe() {
    if (!this.hass || this.gone) return;
    const generation = this.generation;
    try {
      const unsub = await api.subscribeJobs(this.hass, (event) => {
        if (generation === this.generation) this.onEvent(event);
      });
      if (generation !== this.generation) {
        void unsub().catch(() => undefined);
        return;
      }
      this.unsub = unsub;
    } catch {
      if (generation === this.generation) this.scheduleRetry();
    }
  }

  private onEvent(event: SubscribeEvent) {
    if ("snapshot" in event) {
      this.data = normalize(event.snapshot);
      this.reconnecting = false;
      this.attempt = 0;
    } else if ("change" in event) {
      this.data = applyChange(this.data, event.change);
    } else if ("stopped" in event) {
      const unsub = this.unsub;
      this.unsub = undefined;
      void unsub?.().catch(() => undefined);
      this.scheduleRetry();
    }
  }

  private scheduleRetry() {
    this.reconnecting = true;
    if (this.gone) return;
    const delay = nextRetryDelay(this.attempt++);
    window.clearTimeout(this.retryTimer);
    this.retryTimer = window.setTimeout(() => void this.subscribe(), delay);
  }

  private async call<T>(fn: () => Promise<T>) {
    try {
      await fn();
    } catch (err) {
      const message = (err as { message?: string })?.message;
      this.error = message || "Request failed";
    }
  }

  private onRun = (e: CustomEvent<{ job: Job }>) => {
    const hass = this.hass;
    if (hass) void this.call(() => api.runNow(hass, e.detail.job.id));
  };
  private onCancel = (e: CustomEvent<{ job: Job }>) => {
    const hass = this.hass;
    if (hass) void this.call(() => api.cancel(hass, [e.detail.job.id]));
  };
  private onReschedule = (e: CustomEvent<{ job: Job; due: string }>) => {
    const hass = this.hass;
    if (hass) void this.call(() => api.reschedule(hass, e.detail.job.id, e.detail.due));
  };
  private onOpen = (e: CustomEvent<{ job: Job }>) => (this.details = e.detail.job);

  private cancelAll() {
    const hass = this.hass;
    if (!hass) return;
    if (!this.confirmCancelAll) {
      this.confirmCancelAll = true;
      return;
    }
    this.confirmCancelAll = false;
    const ids = this.data.pending.map((j) => j.id);
    if (ids.length) void this.call(() => api.cancel(hass, ids));
  }

  private clearHistory() {
    const hass = this.hass;
    this.confirmCancelAll = false;
    if (hass) void this.call(() => api.clearHistory(hass));
  }

  private onMenuSelect(e: CustomEvent<{ item: { value: string } }>) {
    const value = e.detail.item.value;
    if (value === "cancel-all") {
      // Keep the menu open so the confirmation shows where the user clicked.
      if (!this.confirmCancelAll) e.preventDefault();
      this.cancelAll();
    } else if (value === "clear-history") {
      this.clearHistory();
    }
  }

  private get title_(): string {
    const title = this.panel?.config?.title;
    return typeof title === "string" && title ? title : DEFAULT_TITLE;
  }

  protected override render() {
    if (this.missing === undefined) return nothing;
    if (this.missing.length) {
      return html`<div class="missing">
        <p>This panel needs an update for this Home Assistant version.</p>
        <p>Missing: ${this.missing.join(", ")}</p>
      </div>`;
    }
    const isAdmin = this.atInfo?.is_admin ?? false;
    return html`
      <hass-subpage main-page .hass=${this.hass} .narrow=${this.narrow} .header=${this.title_}>
        <ha-dropdown
          slot="toolbar-icon"
          placement="bottom-end"
          @wa-select=${this.onMenuSelect}
          @wa-after-hide=${() => (this.confirmCancelAll = false)}
        >
          <ha-icon-button slot="trigger" .label=${"More options"} .path=${mdiDotsVertical}></ha-icon-button>
          <ha-dropdown-item value="cancel-all">${this.confirmCancelAll ? "Confirm cancel all?" : "Cancel all"}</ha-dropdown-item>
          <ha-dropdown-item value="clear-history">Clear history</ha-dropdown-item>
        </ha-dropdown>
        <div class="content" @run-job=${this.onRun} @cancel-job=${this.onCancel} @reschedule-job=${this.onReschedule} @open-job=${this.onOpen}>
          ${this.reconnecting ? html`<div class="notice">Reconnecting…</div>` : nothing}
          ${this.error
            ? html`<div class="error" role="alert">${this.error}<button aria-label="Dismiss" @click=${() => (this.error = "")}>✕</button></div>`
            : nothing}
          <at-upcoming-table
            .hass=${this.hass}
            .pending=${this.data.pending}
            .running=${this.data.running}
            .now=${this.now}
            .isAdmin=${isAdmin}
            .narrow=${this.narrow}
          ></at-upcoming-table>
          <at-history-table .hass=${this.hass} .history=${this.data.history} .now=${this.now} .narrow=${this.narrow}></at-history-table>
        </div>
        <ha-button slot="fab" size="l" @click=${() => (this.addOpen = true)}>
          <ha-svg-icon slot="start" .path=${mdiPlus}></ha-svg-icon>
          Add job
        </ha-button>
      </hass-subpage>
      <at-add-job-dialog .hass=${this.hass} .isAdmin=${isAdmin} .open=${this.addOpen} @close-add-job=${() => (this.addOpen = false)}></at-add-job-dialog>
      <at-job-details .hass=${this.hass} .job=${this.details} @close-details=${() => (this.details = undefined)}></at-job-details>
    `;
  }

  static override styles = css`
    :host {
      display: block;
      height: 100vh;
      height: 100dvh;
    }
    .content {
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      gap: 16px;
      max-width: 1000px;
      margin: 0 auto;
      padding: 16px 16px 88px;
    }
    .notice {
      color: var(--secondary-text-color);
    }
    .error {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      border-radius: 4px;
      color: var(--text-primary-color);
      background: var(--error-color);
    }
    .error button {
      font: inherit;
      color: inherit;
      background: none;
      border: none;
      cursor: pointer;
    }
    .missing {
      padding: 32px 16px;
      color: var(--primary-text-color);
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "at-panel": AtPanel;
  }
}
