/**
 * Loads Home Assistant's list-page elements for the panel.
 *
 * These elements are code-split and only register when a built-in page using them opens, so the panel asks HA's
 * panel resolver to load the config panel and its automation page first. That relies on HA frontend internals
 * (`partial-panel-resolver._getRoutes`, `ha-panel-config.routerOptions`), verified against HA 2026.10.4. When it
 * stops working, the panel reports which elements are missing instead of rendering a half-built page.
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

type Loadable = { load: () => Promise<unknown> };

async function triggerConfigPanelLoad(): Promise<void> {
  const resolver = document.createElement("partial-panel-resolver") as HTMLElement & {
    hass?: unknown;
    _getRoutes(panels: unknown): { routes: Record<string, Loadable> };
  };
  const panels = { config: { component_name: "config", url_path: "config" } };
  resolver.hass = { panels };
  await resolver._getRoutes(panels).routes.config.load();
  await customElements.whenDefined("ha-panel-config");
  const config = document.createElement("ha-panel-config") as HTMLElement & {
    routerOptions: { routes: Record<string, Loadable> };
  };
  await config.routerOptions.routes.automation.load();
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
