"""Shared fixtures for the at tests."""

from collections.abc import Generator
import logging

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.at.const import DISPLAY_NAME, DOMAIN
from homeassistant.core import HomeAssistant


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Load custom integrations in every test."""


@pytest.fixture(autouse=True)
def mark_manifest_dependencies_loaded(request: pytest.FixtureRequest) -> None:
    """
    Treat the heavy manifest dependencies as set up, so tests do not start a real HTTP server.

    Marking a component loaded bypasses its own dependency setup. A test that needs the real
    conversation, intent, frontend or panel_custom setup opts out with @pytest.mark.real_dependencies.
    """
    if "hass" not in request.fixturenames or request.node.get_closest_marker("real_dependencies"):
        return
    hass: HomeAssistant = request.getfixturevalue("hass")
    hass.config.components.update({"conversation", "intent", "http", "frontend", "panel_custom"})


@pytest.fixture(autouse=True)
def fail_on_deprecation_report(caplog: pytest.LogCaptureFixture) -> Generator[None]:
    """Fail a test when Home Assistant logs a deprecation this integration caused."""
    yield
    reports = [
        message
        for record in [*caplog.get_records("setup"), *caplog.get_records("call")]
        if record.levelno >= logging.WARNING
        and DOMAIN in (message := record.getMessage())
        and message.startswith(("Detected that custom integration", "The deprecated"))
    ]
    assert not reports, "\n".join(reports)


@pytest.fixture
def config_entry(request: pytest.FixtureRequest) -> MockConfigEntry:
    """Return a config entry for this integration; parametrize it indirectly to set its options."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=DISPLAY_NAME,
        data={},
        options=getattr(request, "param", {}),
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> MockConfigEntry:
    """
    Set up the integration from a config entry.

    Returns:
        The config entry, now loaded.

    """
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
