"""Shared fixtures for the at tests."""

from collections.abc import Generator
import logging
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.at.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

# The response the demo endpoint returns; the client turns it into the device payload.
API_RESPONSE: dict[str, Any] = {"userId": 1, "id": 1, "title": "demo", "body": "demo"}


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
def mock_api() -> Generator[AsyncMock]:
    """Replace the client's HTTP layer, keeping its payload logic under test."""
    with patch(
        "custom_components.at.api.client.AtApiClient._api_wrapper",
        new_callable=AsyncMock,
        return_value=API_RESPONSE,
    ) as api_wrapper:
        yield api_wrapper


@pytest.fixture
def config_entry(request: pytest.FixtureRequest) -> MockConfigEntry:
    """Return a config entry for this integration; parametrize it indirectly to set its options."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="demo",
        unique_id="demo",
        data={CONF_USERNAME: "demo", CONF_PASSWORD: "secret"},
        options=getattr(request, "param", {}),
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_api: AsyncMock,
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
