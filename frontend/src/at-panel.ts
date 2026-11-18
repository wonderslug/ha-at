import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, PanelInfo } from "./types";

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
        <button class="add">+ Add job</button>
        <div class="menu-wrap">
          <button class="menu" aria-label="More options" @click=${() => (this.menuOpen = !this.menuOpen)}>⋮</button>
          ${this.menuOpen ? html`<div class="menu-pop" role="menu"></div>` : nothing}
        </div>
      </header>
      <main></main>
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
