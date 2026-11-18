import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import * as api from "../api";
import { buildPickedAction, isFuture, parseJsonObject, parseRawAction, quickDue, type Verb } from "../add-job";
import { dateToWallTime, formatWhen, wallTimeToDate } from "../format";
import type { HomeAssistant, SchedulePayload } from "../types";

type Mode = "type" | "pick" | "raw";
type Op = Verb | "script" | "automation";
type Preview = { ok: true; text: string } | { ok: false; message: string };

const TOGGLE_DOMAINS = ["light", "switch", "fan", "cover", "input_boolean", "climate", "media_player", "lock", "humidifier", "siren", "vacuum"];

/**
 * Add job dialog. Pickers are plain <select>s built from `hass.states`: they work without HA's
 * lazily loaded `ha-selector`, which a custom panel cannot rely on being registered.
 */
@customElement("at-add-job-dialog")
export class AddJobDialog extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @property({ type: Boolean }) isAdmin = false;
  @property({ type: Boolean, reflect: true }) open = false;

  @state() private mode: Mode = "type";
  @state() private text = "";
  @state() private preview?: Preview;
  @state() private op: Op = "turn_on";
  @state() private entity = "";
  @state() private varsText = "";
  @state() private chip: "+15m" | "+1h" | "" = "+15m";
  @state() private when = "";
  @state() private rawText = "";
  @state() private error = "";
  @state() private busy = false;

  private debounce?: number;
  private parseSeq = 0;

  private onKey = (e: KeyboardEvent) => {
    if (e.key === "Escape" && this.open) this.close();
  };

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
    if (changed.has("open") && this.open) this.reset();
  }

  private reset() {
    window.clearTimeout(this.debounce);
    this.parseSeq++;
    this.mode = "type";
    this.text = "";
    this.preview = undefined;
    this.op = "turn_on";
    this.entity = "";
    this.varsText = "";
    this.chip = "+15m";
    this.when = "";
    this.rawText = "";
    this.error = "";
    this.busy = false;
  }

  private close() {
    this.reset();
    this.open = false;
    this.dispatchEvent(new CustomEvent("close-add-job"));
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

  private get domains(): string[] {
    return this.op === "script" ? ["script"] : this.op === "automation" ? ["automation"] : TOGGLE_DOMAINS;
  }

  private get entities(): { id: string; name: string }[] {
    const states = this.hass?.states ?? {};
    return Object.entries(states)
      .filter(([id]) => this.domains.includes(id.split(".")[0]))
      .map(([id, s]) => ({ id, name: s.attributes.friendly_name || id }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  private get vars() {
    return this.op === "script" ? parseJsonObject(this.varsText) : ({ ok: true, value: {} } as const);
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
    if (this.mode === "raw") return this.rawText.trim() !== "" && this.whenValid;
    return this.entity !== "" && this.vars.ok && this.whenValid;
  }

  private buildPayload(): SchedulePayload | string {
    if (this.mode === "type") return { text: this.text };
    const raw = this.mode === "raw";
    let action: Record<string, unknown>[];
    if (raw) {
      const r = parseRawAction(this.rawText);
      if (!r.ok) return r.error;
      action = r.value;
    } else if (this.op === "script") {
      const v = parseJsonObject(this.varsText);
      if (!v.ok) return v.error;
      action = buildPickedAction({ script: this.entity, variables: v.value });
    } else if (this.op === "automation") {
      action = buildPickedAction({ automation: this.entity });
    } else {
      action = buildPickedAction({ targetEntityIds: [this.entity], verb: this.op });
    }
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

  private pickSection() {
    const needsVars = this.op === "script";
    const vars = this.vars;
    return html`
      <div class="field">
        <label class="label" for="op">Action</label>
        <select id="op" .value=${this.op} @change=${(e: Event) => {
          this.op = (e.target as HTMLSelectElement).value as Op;
          this.entity = "";
        }}>
          <option value="turn_on">Turn on</option>
          <option value="turn_off">Turn off</option>
          <option value="toggle">Toggle</option>
          <option value="script">Run script</option>
          <option value="automation">Trigger automation</option>
        </select>
      </div>
      <div class="field">
        <label class="label" for="entity">Target</label>
        <select id="entity" .value=${this.entity} @change=${(e: Event) => (this.entity = (e.target as HTMLSelectElement).value)}>
          <option value="">Choose…</option>
          ${this.entities.map((e) => html`<option value=${e.id} ?selected=${e.id === this.entity}>${e.name}</option>`)}
        </select>
      </div>
      ${needsVars
        ? html`<div class="field">
            <label class="label" for="vars">Variables (JSON, optional)</label>
            <textarea id="vars" rows="3" placeholder='{"brightness": 80}' .value=${this.varsText} @input=${(e: Event) => (this.varsText = (e.target as HTMLTextAreaElement).value)}></textarea>
            ${!vars.ok ? html`<div class="inline-error">${vars.error}</div>` : nothing}
          </div>`
        : nothing}
      ${this.whenSection()}
    `;
  }

  private typeSection() {
    return html`<div class="field">
      <label class="label" for="text">What should happen, and when?</label>
      <input id="text" type="text" placeholder="turn on the porch light at 11pm" .value=${this.text} @input=${(e: Event) => this.onText((e.target as HTMLInputElement).value)} />
      ${this.preview
        ? html`<div class=${this.preview.ok ? "preview ok" : "preview bad"}>${this.preview.ok ? this.preview.text : this.preview.message}</div>`
        : nothing}
    </div>`;
  }

  private rawSection() {
    const raw = this.rawText.trim() ? parseRawAction(this.rawText) : undefined;
    return html`<div class="field">
        <label class="label" for="raw">Action list (JSON)</label>
        <textarea id="raw" rows="6" placeholder='[{"action": "light.turn_on", "target": {"entity_id": "light.porch"}}]' .value=${this.rawText} @input=${(e: Event) => (this.rawText = (e.target as HTMLTextAreaElement).value)}></textarea>
        ${raw && !raw.ok ? html`<div class="inline-error">${raw.error}</div>` : nothing}
      </div>
      ${this.whenSection()}`;
  }

  private tabBtn(mode: Mode, label: string) {
    return html`<button class="mode ${this.mode === mode ? "active" : ""}" role="tab" aria-selected=${this.mode === mode} @click=${() => this.setMode(mode)}>${label}</button>`;
  }

  protected override render() {
    if (!this.open) return nothing;
    const rawBad = this.mode === "raw" && this.rawText.trim() !== "" && !parseRawAction(this.rawText).ok;
    return html`
      <div class="backdrop" @click=${() => this.close()}></div>
      <div class="dialog" role="dialog" aria-modal="true" aria-label="Add job">
        <h2>Add job</h2>
        <div class="modes" role="tablist">
          ${this.tabBtn("type", "Type it")} ${this.tabBtn("pick", "Pick it")} ${this.isAdmin ? this.tabBtn("raw", "Raw") : nothing}
        </div>
        ${this.mode === "type" ? this.typeSection() : this.mode === "pick" ? this.pickSection() : this.rawSection()}
        ${this.error ? html`<div class="error" role="alert">${this.error}</div>` : nothing}
        <div class="actions">
          <button @click=${() => this.close()}>Cancel</button>
          <button class="primary" ?disabled=${!this.canSubmit || rawBad} @click=${() => void this.submit()}>Add</button>
        </div>
      </div>
    `;
  }

  static override styles = css`
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
      width: min(480px, calc(100vw - 32px));
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
    .field {
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin: 12px 0;
    }
    .label {
      font-size: 13px;
      color: var(--secondary-text-color);
    }
    input,
    select,
    textarea {
      font: inherit;
      padding: 8px;
      color: var(--primary-text-color);
      background: var(--secondary-background-color, transparent);
      border: 1px solid var(--divider-color);
      border-radius: 4px;
    }
    textarea {
      font-family: monospace;
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
    .preview.ok {
      color: var(--success-color, #43a047);
    }
    .preview.bad,
    .inline-error {
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
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "at-add-job-dialog": AddJobDialog;
  }
}
