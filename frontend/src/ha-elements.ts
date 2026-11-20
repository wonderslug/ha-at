/**
 * Loads Home Assistant's list-page elements for the panel.
 *
 * These elements are code-split and only register when a built-in page using them opens, so the panel asks HA's
 * panel resolver to load the config panel and its automation page first. That relies on HA frontend internals
 * (`partial-panel-resolver._getRoutes`, `ha-panel-config.routerOptions`), verified against HA 2026.10.4. When it
 * stops working, the panel reports which elements are missing instead of rendering a half-built page.
 *
 * The Add job dialog's action form and step editor load the same way, on first open, from the config panel's
 * tools/action route or the automation editor; when that fails, the dialog falls back to its plain controls.
 */

export const REQUIRED_ELEMENTS: readonly string[] = [
  "hass-subpage",
  "ha-card",
  "ha-data-table",
  "ha-button",
  "ha-icon-button",
  "ha-dropdown",
  "ha-dropdown-item",
  "ha-svg-icon",
  "ha-filter-chip",
];

export const PICKER_ELEMENTS: readonly string[] = ["ha-service-control", "ha-selector"];

export interface ElementRegistry {
  get(tag: string): unknown;
  whenDefined(tag: string): Promise<unknown>;
}

/** Wait up to `timeoutMs` for every tag to be defined; resolve to the tags still missing. Never rejects. */
export async function waitForElements(registry: ElementRegistry, tags: readonly string[], timeoutMs: number): Promise<string[]> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<void>((resolve) => (timer = setTimeout(resolve, timeoutMs)));
  await Promise.race([Promise.all(tags.map((t) => registry.whenDefined(t).catch(() => undefined))), timeout]);
  clearTimeout(timer);
  return tags.filter((t) => !registry.get(t));
}

type Loadable = { load?: () => Promise<unknown> };
type Routed = HTMLElement & { routerOptions?: { routes: Record<string, Loadable | string | undefined> } };

/** Create `tag` once it is defined and load one of its router's routes, if that route has a loader. */
async function loadSubRoute(tag: string, route: string): Promise<void> {
  await customElements.whenDefined(tag);
  const entry = (document.createElement(tag) as Routed).routerOptions?.routes[route];
  if (typeof entry === "object") await entry.load?.();
}

async function loadConfigPanel(): Promise<void> {
  const resolver = document.createElement("partial-panel-resolver") as HTMLElement & {
    hass?: unknown;
    _getRoutes(panels: unknown): { routes: Record<string, Required<Loadable>> };
  };
  const panels = { config: { component_name: "config", url_path: "config" } };
  resolver.hass = { panels };
  await resolver._getRoutes(panels).routes.config.load();
}

async function triggerConfigPanelLoad(): Promise<void> {
  await loadConfigPanel();
  await loadSubRoute("ha-panel-config", "automation");
}

async function loadToolsAction(): Promise<void> {
  await loadConfigPanel();
  await loadSubRoute("ha-panel-config", "tools");
  await loadSubRoute("ha-panel-tools", "action");
}

async function loadAutomationEditor(): Promise<void> {
  await triggerConfigPanelLoad();
  await loadSubRoute("ha-config-automation", "edit");
}

/**
 * Run `steps` in order, each bounded by `stepTimeoutMs`, until every tag is defined. A step that throws or hangs is
 * an expected miss on some frontend versions, so it is skipped silently; the caller reports tags still missing.
 */
export async function runLoadSteps(
  registry: ElementRegistry,
  tags: readonly string[],
  steps: readonly (() => Promise<void>)[],
  stepTimeoutMs: number,
): Promise<void> {
  for (const step of steps) {
    if (tags.every((t) => registry.get(t))) return;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const expired = new Promise<void>((resolve) => (timer = setTimeout(resolve, stepTimeoutMs)));
    await Promise.race([step().catch(() => undefined), expired]);
    clearTimeout(timer);
  }
}

/**
 * Run `trigger` unless every tag is already defined, then wait for the tags. One deadline covers both phases, so a
 * trigger that hangs still ends in a list of missing tags. Missing tags are logged.
 */
export async function loadElements(
  registry: ElementRegistry,
  trigger: () => Promise<void>,
  tags: readonly string[],
  timeoutMs: number,
): Promise<string[]> {
  const deadline = Date.now() + timeoutMs;
  if (tags.some((t) => !registry.get(t))) {
    let timer: ReturnType<typeof setTimeout> | undefined;
    const expired = new Promise<void>((resolve) => (timer = setTimeout(resolve, timeoutMs)));
    const triggered = trigger().catch((err: unknown) => {
      console.warn("Scheduled Jobs: could not load Home Assistant's panel elements", err);
    });
    await Promise.race([triggered, expired]);
    clearTimeout(timer);
  }
  const missing = await waitForElements(registry, tags, Math.max(0, deadline - Date.now()));
  if (missing.length) console.warn("Scheduled Jobs: Home Assistant elements missing:", missing.join(", "));
  return missing;
}

let loading: Promise<string[]> | undefined;

/** Load HA's elements once per page; resolve to the required tags that never registered. */
export function loadHaElements(timeoutMs = 10_000): Promise<string[]> {
  loading ??= loadElements(customElements, triggerConfigPanelLoad, REQUIRED_ELEMENTS, timeoutMs);
  return loading;
}

let pickerLoading: Promise<string[]> | undefined;

/** Load the Pick it and Sequence tabs' elements once per page; resolve to the tags that never registered. */
export function loadPickerElements(timeoutMs = 10_000): Promise<string[]> {
  const steps = [loadToolsAction, loadAutomationEditor];
  const trigger = () => runLoadSteps(customElements, PICKER_ELEMENTS, steps, timeoutMs / steps.length);
  pickerLoading ??= loadElements(customElements, trigger, PICKER_ELEMENTS, timeoutMs);
  return pickerLoading;
}

/** Whether every element the Pick it tab renders is registered right now. */
export function pickerElementsDefined(registry: ElementRegistry = customElements): boolean {
  return PICKER_ELEMENTS.every((t) => registry.get(t));
}
