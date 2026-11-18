"""Tests for the single-instance config flow."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.at.const import DISPLAY_NAME, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """The flow shows a confirm form, and submitting it creates the entry."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DISPLAY_NAME
    assert result["data"] == {}


async def test_second_flow_aborts(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """A second flow aborts once an entry exists."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow_shows_empty_form(init_integration: MockConfigEntry, hass: HomeAssistant) -> None:
    """The options flow stub returns an empty form."""
    result = await hass.config_entries.options.async_init(init_integration.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
