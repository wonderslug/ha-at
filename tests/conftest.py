"""Shared fixtures for the at tests."""

from collections.abc import Generator
from dataclasses import dataclass
import logging

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.at.const import DISPLAY_NAME, DOMAIN
from homeassistant.components import conversation
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component

ASSISTANT = conversation.DOMAIN


@dataclass
class Assist:
    """What the voice tests share: a satellite in the office and two lights."""

    device_id: str
    turn_on_calls: list[ServiceCall]


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


@pytest.fixture
async def assist(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> Assist:
    """Set up the real conversation stack with an exposed and an unexposed light."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "conversation", {})
    assert await async_setup_component(hass, "intent", {})

    office = area_registry.async_create("Office")
    satellite_entry = MockConfigEntry(domain="test")
    satellite_entry.add_to_hass(hass)
    satellite = device_registry.async_get_or_create(
        config_entry_id=satellite_entry.entry_id, identifiers={("test", "satellite")}
    )
    device_registry.async_update_device(satellite.id, area_id=office.id)

    for object_id, name, exposed in (("kitchen", "Kitchen light", True), ("garage", "Garage light", False)):
        entry = entity_registry.async_get_or_create(
            "light", "test", object_id, suggested_object_id=object_id, original_name=name
        )
        hass.states.async_set(entry.entity_id, "off", {ATTR_FRIENDLY_NAME: name})
        async_expose_entity(hass, ASSISTANT, entry.entity_id, exposed)

    turn_on_calls = async_mock_service(hass, "light", "turn_on")
    await hass.async_block_till_done()
    return Assist(device_id=satellite.id, turn_on_calls=turn_on_calls)
