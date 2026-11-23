import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { parseRawAction } from "../add-job";
import type { Localize } from "../localize";
import type { HomeAssistant } from "../types";
import { fieldStyles } from "./field-styles";

/**
 * The Sequence tab: Home Assistant's action editor (`ha-selector`) when `ready`, a JSON textarea otherwise.
 * Fires `action-changed` with the step list, or `undefined` while it is empty or invalid.
 */
@customElement("at-sequence-editor")
export class SequenceEditor extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @property({ attribute: false }) localize: Localize = (key) => key;
  @property({ type: Boolean }) ready = false;

  @state() private value: unknown[] = [];
  @state() private rawText = "";

  private emit(action: Record<string, unknown>[] | undefined) {
    this.dispatchEvent(new CustomEvent("action-changed", { detail: { action } }));
  }

  private onValue(e: CustomEvent<{ value?: unknown }>) {
    e.stopPropagation();
    const v = e.detail.value;
    this.value = Array.isArray(v) ? v : [];
    this.emit(Array.isArray(v) && v.length > 0 ? (v as Record<string, unknown>[]) : undefined);
  }

  private onRaw(text: string) {
    this.rawText = text;
    const r = parseRawAction(text, this.localize);
    this.emit(r.ok ? r.value : undefined);
  }

  private fallback() {
    const raw = this.rawText.trim() ? parseRawAction(this.rawText, this.localize) : undefined;
    return html`<div class="field">
      <label class="label" for="raw">${this.localize("sequence_editor.action_list")}</label>
      <textarea id="raw" rows="6" placeholder='[{"action": "light.turn_on", "target": {"entity_id": "light.porch"}}]' .value=${this.rawText} @input=${(e: Event) => this.onRaw((e.target as HTMLTextAreaElement).value)}></textarea>
      ${raw && !raw.ok ? html`<div class="inline-error">${raw.error}</div>` : nothing}
    </div>`;
  }

  protected override render() {
    return this.ready
      ? html`<ha-selector .hass=${this.hass} .selector=${{ action: {} }} .value=${this.value} @value-changed=${this.onValue}></ha-selector>`
      : this.fallback();
  }

  static override styles = [
    fieldStyles,
    css`
      :host {
        display: block;
      }
      :host([hidden]) {
        display: none;
      }
    `,
  ];
}

declare global {
  interface HTMLElementTagNameMap {
    "at-sequence-editor": SequenceEditor;
  }
}
