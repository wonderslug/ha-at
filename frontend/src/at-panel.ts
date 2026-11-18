import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import * as api from "./api";
import "./components/add-job-dialog";
import "./components/history-table";
import "./components/job-details";
import "./components/upcoming-table";
import { nextRetryDelay } from "./reconnect";
import { applyChange, normalize, type PanelState } from "./state";
import type { AtInfo, HomeAssistant, Job, PanelInfo, SubscribeEvent } from "./types";

type Tab = "upcoming" | "history";

const DEFAULT_TITLE = "at";

@customElement("at-panel")
export class AtPanel extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @property({ type: Boolean }) narrow = false;
  @property({ attribute: false }) panel?: PanelInfo;
  @property({ attribute: false }) route?: unknown;

  @state() private tab: Tab = "upcoming";
  @state() private menuOpen = false;
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
    this.menuOpen = false;
    const ids = this.data.pending.map((j) => j.id);
    if (ids.length) void this.call(() => api.cancel(hass, ids));
  }

  private clearHistory() {
    const hass = this.hass;
    this.menuOpen = false;
    this.confirmCancelAll = false;
    if (hass) void this.call(() => api.clearHistory(hass));
  }

  private toggleMenu() {
    this.menuOpen = !this.menuOpen;
    this.confirmCancelAll = false;
  }

  private get title_(): string {
    const title = this.panel?.config?.title;
    return typeof title === "string" && title ? title : DEFAULT_TITLE;
  }

  private tabButton(tab: Tab, label: string) {
    return html`<button
      class="tab ${this.tab === tab ? "active" : ""}"
      role="tab"
      aria-selected=${this.tab === tab}
      @click=${() => (this.tab = tab)}
    >
      ${label}
    </button>`;
  }

  protected override render() {
    return html`
      <header>
        <h1>${this.title_}</h1>
        <div class="tabs" role="tablist">${this.tabButton("upcoming", "Upcoming")} ${this.tabButton("history", "History")}</div>
        <button class="add" @click=${() => (this.addOpen = true)}>+ Add job</button>
        <div class="menu-wrap">
          <button class="menu" aria-label="More options" @click=${() => this.toggleMenu()}>⋮</button>
          ${this.menuOpen ? html`<div class="menu-pop" role="menu">
                <button role="menuitem" @click=${() => this.cancelAll()}>${this.confirmCancelAll ? "Confirm cancel all?" : "Cancel all"}</button>
                <button role="menuitem" @click=${() => this.clearHistory()}>Clear history</button>
              </div>` : nothing}
        </div>
      </header>
      ${this.reconnecting ? html`<div class="notice">Reconnecting…</div>` : nothing}
      ${this.error
        ? html`<div class="error" role="alert">${this.error}<button aria-label="Dismiss" @click=${() => (this.error = "")}>✕</button></div>`
        : nothing}
      <main @run-job=${this.onRun} @cancel-job=${this.onCancel} @reschedule-job=${this.onReschedule} @open-job=${this.onOpen}>
        ${this.tab === "upcoming"
          ? html`<at-upcoming-table
              .hass=${this.hass}
              .pending=${this.data.pending}
              .running=${this.data.running}
              .now=${this.now}
              .isAdmin=${this.atInfo?.is_admin ?? false}
            ></at-upcoming-table>`
          : html`<at-history-table .hass=${this.hass} .history=${this.data.history} .now=${this.now}></at-history-table>`}
      </main>
      <at-add-job-dialog
        .hass=${this.hass}
        .isAdmin=${this.atInfo?.is_admin ?? false}
        .open=${this.addOpen}
        @close-add-job=${() => (this.addOpen = false)}
      ></at-add-job-dialog>
      <at-job-details .hass=${this.hass} .job=${this.details} @close-details=${() => (this.details = undefined)}></at-job-details>
    `;
  }

  static override styles = css`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
      font-family: var(--paper-font-body1_-_font-family, inherit);
    }
    header {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px 16px;
      background: var(--card-background-color);
      border-bottom: 1px solid var(--divider-color);
    }
    h1 {
      margin: 0;
      font-size: 20px;
      font-weight: 400;
      flex: 1;
    }
    button {
      font: inherit;
      color: var(--primary-text-color);
      background: none;
      border: none;
      cursor: pointer;
    }
    .tabs {
      display: flex;
      gap: 4px;
    }
    .tab {
      padding: 10px 14px;
      border-bottom: 2px solid transparent;
    }
    .tab.active {
      color: var(--primary-color);
      border-bottom-color: var(--primary-color);
    }
    .add {
      padding: 8px 14px;
      border-radius: 18px;
      color: var(--text-primary-color, #fff);
      background: var(--primary-color);
    }
    .menu-wrap {
      position: relative;
    }
    .menu {
      font-size: 20px;
      padding: 4px 8px;
    }
    .menu-pop {
      position: absolute;
      right: 0;
      top: 100%;
      min-width: 160px;
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 4px;
    }
    main {
      padding: 16px;
    }
    .menu-pop button {
      display: block;
      width: 100%;
      text-align: left;
      padding: 10px 14px;
    }
    .notice {
      margin: 8px 16px 0;
      padding: 6px 12px;
      font-size: 13px;
      color: var(--secondary-text-color);
    }
    .error {
      display: flex;
      justify-content: space-between;
      margin: 8px 16px 0;
      padding: 8px 12px;
      border-radius: 4px;
      color: #fff;
      background: var(--error-color, #db4437);
    }
    .error button {
      color: inherit;
    }
    @media (max-width: 600px) {
      header {
        flex-wrap: wrap;
      }
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "at-panel": AtPanel;
  }
}
