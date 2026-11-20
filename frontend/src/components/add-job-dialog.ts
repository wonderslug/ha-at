import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import * as api from "../api";
import { isFuture, quickDue } from "../add-job";
import { dateToWallTime, formatWhen, wallTimeToDate } from "../format";
import { loadPickerElements, pickerElementsDefined } from "../ha-elements";
import type { HomeAssistant, SchedulePayload } from "../types";
import { fieldStyles } from "./field-styles";
import "./pick-action";
import "./sequence-editor";

type Mode = "type" | "pick" | "sequence";
type Preview = { ok: true; text: string } | { ok: false; message: string };

/**
 * Add job dialog. Pick it and Sequence use Home Assistant's action form and editor, loaded on first open; whether it
 * loaded is decided once per open, so the tab never swaps its controls under the user.
 */
@customElement("at-add-job-dialog")
export class AddJobDialog extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @property({ type: Boolean }) isAdmin = false;
  @property({ type: Boolean, reflect: true }) open = false;

  @state() private mode: Mode = "type";
  @state() private text = "";
  @state() private preview?: Preview;
  @state() private pickerReady?: boolean;
  @state() private pickedAction?: Record<string, unknown>[];
  @state() private sequenceAction?: Record<string, unknown>[];
  @state() private chip: "+15m" | "+1h" | "" = "+15m";
  @state() private when = "";
  @state() private error = "";
  @state() private busy = false;

  private debounce?: number;
  private parseSeq = 0;
  private openSeq = 0;
  private returnFocus?: HTMLElement;

  private onKey = (e: KeyboardEvent) => {
    if (!this.open) return;
    if (e.key === "Escape" && !e.defaultPrevented && !this.inPopup(e)) this.close();
    else if (e.key === "Tab" && !this.inOverlay(e)) this.trapFocus(e);
  };

  /** An Escape meant for an open HA popup, inside the dialog or outside it; ancestors of the dialog do not count. */
  private inPopup(e: KeyboardEvent): boolean {
    const path = e.composedPath();
    const host = path.indexOf(this);
    return (host === -1 ? path : path.slice(0, host)).some(
      (n) => n instanceof Element && (n.getAttribute("aria-expanded") === "true" || n.hasAttribute("open")),
    );
  }

  /** Focus in an HA overlay outside the dialog's shadow root, which manages its own Tab order. */
  private inOverlay(e: KeyboardEvent): boolean {
    const path = e.composedPath();
    const origin = path[0];
    return origin instanceof Element && origin !== document.body && !path.includes(this);
  }

  override connectedCallback() {
    super.connectedCallback();
    window.addEventListener("keydown", this.onKey);
  }

  override disconnectedCallback() {
    super.disconnectedCallback();
    window.removeEventListener("keydown", this.onKey);
    window.clearTimeout(this.debounce);
  }

  protected override updated(changed: Map<string, unknown>) {
    if (changed.has("open") && this.open) {
      this.returnFocus = deepActiveElement();
      this.reset();
      this.decidePicker();
      const dialog = this.shadowRoot?.querySelector(".dialog");
      (dialog?.querySelector<HTMLElement>("input, select, textarea") ?? this.focusables()[0])?.focus();
    }
  }

  private decidePicker() {
    const seq = ++this.openSeq;
    void loadPickerElements().then(() => {
      if (seq === this.openSeq && this.open && this.pickerReady === undefined) this.pickerReady = pickerElementsDefined();
    });
  }

  private focusables(): HTMLElement[] {
    const dialog = this.shadowRoot?.querySelector(".dialog");
    if (!dialog) return [];
    return [...dialog.querySelectorAll<HTMLElement>("button, input, select, textarea")].filter(
      (el) => !(el as HTMLButtonElement).disabled,
    );
  }

  /** Keep Tab and Shift+Tab inside the dialog, which is modal. */
  private trapFocus(e: KeyboardEvent) {
    const items = this.focusables();
    if (!items.length) return;
    const active = this.shadowRoot?.activeElement as HTMLElement | null;
    const inside = active !== null && !!this.shadowRoot?.querySelector(".dialog")?.contains(active);
    const first = items[0];
    const last = items[items.length - 1];
    if (e.shiftKey && (!inside || active === first)) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && (!inside || active === last)) {
      e.preventDefault();
      first.focus();
    }
  }

  private reset() {
    window.clearTimeout(this.debounce);
    this.parseSeq++;
    this.mode = "type";
    this.text = "";
    this.preview = undefined;
    this.pickerReady = undefined;
    this.pickedAction = undefined;
    this.sequenceAction = undefined;
    this.chip = "+15m";
    this.when = "";
    this.error = "";
    this.busy = false;
  }

  /** Close and reset, except while a submit is in flight: closing then would let it be sent twice. */
  private close() {
    if (this.busy) return;
    this.reset();
    this.open = false;
    this.dispatchEvent(new CustomEvent("close-add-job"));
    this.returnFocus?.focus();
    this.returnFocus = undefined;
  }

  private onText(value: string) {
    this.text = value;
    this.preview = undefined;
    this.error = "";
    window.clearTimeout(this.debounce);
    const seq = ++this.parseSeq;
    if (!value.trim() || !this.hass) return;
    const hass = this.hass;
    this.debounce = window.setTimeout(() => {
      api.parse(hass, value).then(
        (r) => {
          if (seq !== this.parseSeq) return;
          if (r.ok) {
            const when = formatWhen(new Date(r.due), new Date(), this.locale, hass.config.time_zone);
            this.preview = { ok: true, text: `${r.summary} · ${when} ✓` };
          } else {
            this.preview = { ok: false, message: r.message };
          }
        },
        (err: { message?: string }) => {
          if (seq === this.parseSeq) this.preview = { ok: false, message: err?.message || "Could not parse" };
        },
      );
    }, 300);
  }

  private get locale(): string {
    return this.hass?.locale?.language ?? this.hass?.language ?? "en";
  }

  private get whenValid(): boolean {
    return this.chip !== "" || isFuture(this.dueDate(), new Date());
  }

  private dueDate(): Date {
    return wallTimeToDate(this.when, this.hass?.config.time_zone ?? "UTC");
  }

  private get canSubmit(): boolean {
    if (this.busy || !this.hass) return false;
    if (this.mode === "type") return this.preview?.ok === true;
    if (this.mode === "sequence") {
      return this.sequenceAction !== undefined && this.sequenceAction.length > 0 && this.whenValid;
    }
    return this.pickedAction !== undefined && this.whenValid;
  }

  private buildPayload(): SchedulePayload | string {
    if (this.mode === "type") return { text: this.text };
    const action = this.mode === "sequence" ? this.sequenceAction : this.pickedAction;
    if (!action) return "Choose an action";
    if (this.chip) return { action, ...quickDue(this.chip, new Date()) };
    return { action, due: this.dueDate().toISOString() };
  }

  private async submit() {
    const hass = this.hass;
    if (!hass || !this.canSubmit) return;
    const payload = this.buildPayload();
    if (typeof payload === "string") {
      this.error = payload;
      return;
    }
    this.busy = true;
    this.error = "";
    try {
      await api.schedule(hass, payload);
      this.busy = false;
      this.close();
    } catch (err) {
      this.error = (err as { message?: string })?.message || "Could not add the job";
    } finally {
      this.busy = false;
    }
  }

  private setMode(mode: Mode) {
    this.mode = mode;
    this.error = "";
  }

  private onChip(chip: "+15m" | "+1h") {
    this.chip = chip;
    this.when = "";
  }

  private onWhen(value: string) {
    this.when = value;
    this.chip = value ? "" : "+15m";
  }

  private whenSection() {
    const tz = this.hass?.config.time_zone ?? "UTC";
    const min = dateToWallTime(new Date(), tz);
    return html`<div class="field">
      <span class="label">When</span>
      <div class="row">
        ${(["+15m", "+1h"] as const).map(
          (c) => html`<button class="chip ${this.chip === c ? "on" : ""}" @click=${() => this.onChip(c)}>${c}</button>`,
        )}
        <input type="datetime-local" aria-label="Date and time" .value=${this.when} min=${min} @input=${(e: Event) => this.onWhen((e.target as HTMLInputElement).value)} />
      </div>
      ${this.chip === "" && !this.whenValid ? html`<div class="inline-error">${this.when ? "Time must be in the future" : "Choose a time"}</div>` : nothing}
    </div>`;
  }

  /** Kept rendered while another tab shows, so switching tabs keeps what was picked. */
  private pickSection() {
    const shown = this.mode === "pick";
    if (this.pickerReady === undefined) return shown ? html`<div class="field label" role="status">Loading…</div>` : nothing;
    return html`<at-pick-action
      ?hidden=${!shown}
      .hass=${this.hass}
      .ready=${this.pickerReady}
      @action-changed=${(e: CustomEvent<{ action?: Record<string, unknown>[] }>) => (this.pickedAction = e.detail.action)}
    ></at-pick-action>`;
  }

  private typeSection() {
    return html`<div class="field">
      <label class="label" for="text">What should happen, and when?</label>
      <input id="text" type="text" placeholder="turn on the porch light at 11pm" .value=${this.text} @input=${(e: Event) => this.onText((e.target as HTMLInputElement).value)} />
      <div class=${this.preview ? (this.preview.ok ? "preview ok" : "preview bad") : "preview"} aria-live="polite">
        ${this.preview ? (this.preview.ok ? this.preview.text : this.preview.message) : nothing}
      </div>
    </div>`;
  }

  /** Kept rendered while another tab shows, so a half-built sequence survives a tab switch. */
  private sequenceSection() {
    const shown = this.mode === "sequence";
    if (this.pickerReady === undefined) return shown ? html`<div class="field label" role="status">Loading…</div>` : nothing;
    return html`<at-sequence-editor
      ?hidden=${!shown}
      .hass=${this.hass}
      .ready=${this.pickerReady}
      @action-changed=${(e: CustomEvent<{ action?: Record<string, unknown>[] }>) => (this.sequenceAction = e.detail.action)}
    ></at-sequence-editor>`;
  }

  private tabBtn(mode: Mode, label: string) {
    return html`<button class="mode ${this.mode === mode ? "active" : ""}" role="tab" aria-selected=${this.mode === mode} @click=${() => this.setMode(mode)}>${label}</button>`;
  }

  protected override render() {
    if (!this.open) return nothing;
    return html`
      <div class="backdrop" @click=${() => this.close()}></div>
      <div class="dialog" role="dialog" aria-modal="true" aria-label="Add job">
        <h2>Add job</h2>
        <div class="modes" role="tablist">
          ${this.tabBtn("type", "Type it")} ${this.tabBtn("pick", "Pick it")} ${this.isAdmin ? this.tabBtn("sequence", "Sequence") : nothing}
        </div>
        ${this.mode === "type" ? this.typeSection() : nothing} ${this.pickSection()} ${this.isAdmin ? this.sequenceSection() : nothing}
        ${this.mode === "type" ? nothing : this.whenSection()}
        ${this.error ? html`<div class="error" role="alert">${this.error}</div>` : nothing}
        <div class="actions">
          <button ?disabled=${this.busy} @click=${() => this.close()}>Cancel</button>
          <button class="primary" ?disabled=${!this.canSubmit} @click=${() => void this.submit()}>Add</button>
        </div>
      </div>
    `;
  }

  static override styles = [
    fieldStyles,
    css`
      .backdrop {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 10;
      }
      .dialog {
        position: fixed;
        z-index: 11;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: min(640px, calc(100vw - 32px));
        max-height: calc(100vh - 32px);
        overflow: auto;
        box-sizing: border-box;
        padding: 16px 20px;
        background: var(--card-background-color);
        color: var(--primary-text-color);
        border-radius: 8px;
      }
      h2 {
        margin: 0 0 8px;
        font-size: 20px;
        font-weight: 400;
      }
      button {
        font: inherit;
        color: var(--primary-text-color);
        background: none;
        border: none;
        cursor: pointer;
        padding: 8px 12px;
      }
      .modes {
        display: flex;
        gap: 4px;
        margin-bottom: 8px;
      }
      .mode.active {
        color: var(--primary-color);
        border-bottom: 2px solid var(--primary-color);
      }
      .row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
      }
      .chip {
        border: 1px solid var(--divider-color);
        border-radius: 16px;
      }
      .chip.on {
        color: var(--text-primary-color, #fff);
        background: var(--primary-color);
      }
      .preview {
        min-height: 20px;
        line-height: 20px;
      }
      .preview.ok {
        color: var(--success-color, #43a047);
      }
      .preview.bad {
        color: var(--error-color, #db4437);
        font-size: 13px;
      }
      .error {
        margin: 8px 0;
        padding: 8px 12px;
        border-radius: 4px;
        color: #fff;
        background: var(--error-color, #db4437);
      }
      .actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        margin-top: 8px;
      }
      .primary {
        color: var(--text-primary-color, #fff);
        background: var(--primary-color);
        border-radius: 4px;
      }
      .primary[disabled] {
        opacity: 0.5;
        cursor: default;
      }
    `,
  ];
}

function deepActiveElement(): HTMLElement | undefined {
  let active = document.activeElement;
  while (active?.shadowRoot?.activeElement) active = active.shadowRoot.activeElement;
  return active instanceof HTMLElement ? active : undefined;
}

declare global {
  interface HTMLElementTagNameMap {
    "at-add-job-dialog": AddJobDialog;
  }
}
