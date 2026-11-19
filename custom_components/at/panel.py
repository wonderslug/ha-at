"""The `at` sidebar panel: a single-file web component served from this integration."""

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http.server import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import CONF_PANEL_ADMIN_ONLY, DEFAULT_PANEL_ADMIN_ONLY, DOMAIN
from .data import AtConfigEntry

PANEL_URL_PATH = "at"
PANEL_TITLE = "Scheduled Jobs"
STATIC_URL = "/at_static"
FRONTEND_DIR = Path(__file__).parent / "frontend"
_STATIC_REGISTERED = f"{DOMAIN}_static_registered"


async def async_register_panel(hass: HomeAssistant, entry: AtConfigEntry) -> None:
    """Serve the bundle and add the sidebar panel."""
    if not hass.data.get(_STATIC_REGISTERED):
        # Static paths cannot be unregistered, so a reload must not add this one again.
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(FRONTEND_DIR), cache_headers=False)]
        )
        hass.data[_STATIC_REGISTERED] = True
    version = (await async_get_integration(hass, DOMAIN)).version
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name="at-panel",
        module_url=f"{STATIC_URL}/at-panel.js?v={version}",
        sidebar_title=PANEL_TITLE,
        sidebar_icon="mdi:clock-start",
        require_admin=entry.options.get(CONF_PANEL_ADMIN_ONLY, DEFAULT_PANEL_ADMIN_ONLY),
    )


def async_remove_panel(hass: HomeAssistant) -> None:
    """Remove the sidebar panel."""
    frontend.async_remove_panel(hass, PANEL_URL_PATH)
