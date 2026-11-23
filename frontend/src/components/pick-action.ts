import { LitElement, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { fromServiceControl, type ServiceControlValue } from "../add-job";
import type { Localize } from "../localize";
import type { HomeAssistant } from "../types";
import "./pick-fallback";

/**
 * The Pick it tab: Home Assistant's `ha-service-control` when `ready`, the plain fallback controls otherwise.
 * Fires `action-changed` with a one-step action list, or `undefined` while no action is chosen.
 */
@customElement("at-pick-action")
export class PickAction extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @property({ attribute: false }) localize: Localize = (key) => key;
  @property({ type: Boolean }) ready = false;

  @state() private value?: ServiceControlValue;

  private emit(action: Record<string, unknown>[] | undefined) {
    this.dispatchEvent(new CustomEvent("action-changed", { detail: { action } }));
  }

  private onValue(e: CustomEvent<{ value?: ServiceControlValue }>) {
    e.stopPropagation();
    this.value = e.detail.value;
    this.emit(fromServiceControl(this.value));
  }

  private onFallback(e: CustomEvent<{ action?: Record<string, unknown>[] }>) {
    this.emit(e.detail.action);
  }

  protected override render() {
    return this.ready
      ? html`<ha-service-control .hass=${this.hass} .value=${this.value} narrow @value-changed=${this.onValue}></ha-service-control>`
      : html`<at-pick-fallback .hass=${this.hass} .localize=${this.localize} @action-changed=${this.onFallback}></at-pick-fallback>`;
  }

  static override styles = css`
    :host {
      display: block;
    }
    :host([hidden]) {
      display: none;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "at-pick-action": PickAction;
  }
}
