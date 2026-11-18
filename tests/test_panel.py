"""Tests for the sidebar panel registration."""

from pathlib import Path

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.at.const import CONF_PANEL_ADMIN_ONLY, DOMAIN
from homeassistant.components.frontend import DATA_PANELS
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

pytestmark = [
    pytest.mark.real_dependencies,
    pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning"),
]


async def _setup(hass: HomeAssistant, options: dict) -> MockConfigEntry:
    hass.config.components.update({"conversation", "intent"})  # the panel needs neither
    for component in ("http", "frontend", "panel_custom"):
        assert await async_setup_component(hass, component, {})
    entry = MockConfigEntry(domain=DOMAIN, data={}, options=options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_panel_registered_and_removed(hass: HomeAssistant) -> None:
    """The panel is in the sidebar after setup, open to everyone, and gone after unload."""
    entry = await _setup(hass, {})
    panel = hass.data[DATA_PANELS][DOMAIN]
    response = panel.to_response()
    assert panel.require_admin is False
    assert response["config"]["_panel_custom"]["name"] == "at-panel"
    assert response["config"]["_panel_custom"]["module_url"].startswith("/at_static/at-panel.js?v=")
    assert panel.sidebar_icon == "mdi:clock-start"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert DOMAIN not in hass.data[DATA_PANELS]

    # Reloading registers the panel again without a second static path.
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert DOMAIN in hass.data[DATA_PANELS]


@pytest.mark.parametrize(("admin_only", "expected"), [(True, True), (False, False)])
async def test_panel_require_admin_option(hass: HomeAssistant, admin_only: bool, expected: bool) -> None:
    """The panel_admin_only option sets require_admin."""
    await _setup(hass, {CONF_PANEL_ADMIN_ONLY: admin_only})
    assert hass.data[DATA_PANELS][DOMAIN].require_admin is expected


async def test_built_bundle_is_committed() -> None:
    """The single-file bundle HACS installs exists."""
    bundle = Path(__file__).parent.parent / "custom_components" / "at" / "frontend" / "at-panel.js"
    assert bundle.is_file()
