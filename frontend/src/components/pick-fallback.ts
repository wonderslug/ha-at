import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { buildPickedAction, parseJsonObject, type Verb } from "../add-job";
import type { Localize } from "../localize";
import type { HomeAssistant } from "../types";
import { fieldStyles } from "./field-styles";

type Op = Verb | "script" | "automation";

const TOGGLE_DOMAINS = ["light", "switch", "fan", "cover", "input_boolean", "climate", "media_player", "lock", "humidifier", "siren", "vacuum"];

/**
 * Plain verb, target and variables controls built from `hass.states`, for when Home Assistant's action form did not
 * load. Fires `action-changed` with the picked action, or `undefined` while it is incomplete.
 */
@customElement("at-pick-fallback")
export class PickFallback extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @property({ attribute: false }) localize: Localize = (key) => key;

  @state() private op: Op = "turn_on";
  @state() private entity = "";
  @state() private varsText = "";

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
    return this.op === "script" ? parseJsonObject(this.varsText, this.localize) : ({ ok: true, value: {} } as const);
  }

  private get action(): Record<string, unknown>[] | undefined {
    const vars = this.vars;
    if (this.entity === "" || !vars.ok) return undefined;
    if (this.op === "script") return buildPickedAction({ script: this.entity, variables: vars.value });
    if (this.op === "automation") return buildPickedAction({ automation: this.entity });
    return buildPickedAction({ targetEntityIds: [this.entity], verb: this.op });
  }

  protected override updated(changed: Map<string, unknown>) {
    if (changed.has("op") || changed.has("entity") || changed.has("varsText")) {
      this.dispatchEvent(new CustomEvent("action-changed", { detail: { action: this.action } }));
    }
  }

  protected override render() {
    const vars = this.vars;
    return html`
      <div class="field">
        <label class="label" for="op">${this.localize("pick_fallback.action")}</label>
        <select id="op" .value=${this.op} @change=${(e: Event) => {
          this.op = (e.target as HTMLSelectElement).value as Op;
          this.entity = "";
        }}>
          <option value="turn_on">${this.localize("pick_fallback.op_turn_on")}</option>
          <option value="turn_off">${this.localize("pick_fallback.op_turn_off")}</option>
          <option value="toggle">${this.localize("pick_fallback.op_toggle")}</option>
          <option value="script">${this.localize("pick_fallback.op_script")}</option>
          <option value="automation">${this.localize("pick_fallback.op_automation")}</option>
        </select>
      </div>
      <div class="field">
        <label class="label" for="entity">${this.localize("pick_fallback.target")}</label>
        <select id="entity" .value=${this.entity} @change=${(e: Event) => (this.entity = (e.target as HTMLSelectElement).value)}>
          <option value="">${this.localize("pick_fallback.choose")}</option>
          ${this.entities.map((e) => html`<option value=${e.id} ?selected=${e.id === this.entity}>${e.name}</option>`)}
        </select>
      </div>
      ${this.op === "script"
        ? html`<div class="field">
            <label class="label" for="vars">${this.localize("pick_fallback.variables")}</label>
            <textarea id="vars" rows="3" placeholder='{"brightness": 80}' .value=${this.varsText} @input=${(e: Event) => (this.varsText = (e.target as HTMLTextAreaElement).value)}></textarea>
            ${!vars.ok ? html`<div class="inline-error">${vars.error}</div>` : nothing}
          </div>`
        : nothing}
    `;
  }

  static override styles = [
    fieldStyles,
    css`
      :host {
        display: block;
      }
    `,
  ];
}

declare global {
  interface HTMLElementTagNameMap {
    "at-pick-fallback": PickFallback;
  }
}
