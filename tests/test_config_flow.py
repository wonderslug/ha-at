"""Tests for the single-instance config flow and its options."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.at.const import (
    CONF_DEFER_RELATIVE,
    CONF_GRACE_MINUTES,
    CONF_HISTORY_DAYS,
    CONF_HISTORY_MAX,
    CONF_PANEL_ADMIN_ONLY,
    DEFAULT_DEFER_RELATIVE,
    DEFAULT_GRACE_MINUTES,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_HISTORY_MAX,
    DEFAULT_PANEL_ADMIN_ONLY,
    DISPLAY_NAME,
    DOMAIN,
)
from custom_components.at.core.manager import JobManager, ManagerOptions
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from tests.assist import Assist, say  # noqa: TID251  (plain module; see tests/assist.py)

NEW_OPTIONS = {
    CONF_GRACE_MINUTES: 10,
    CONF_HISTORY_DAYS: 3,
    CONF_HISTORY_MAX: 20,
    CONF_PANEL_ADMIN_ONLY: True,
    CONF_DEFER_RELATIVE: True,
}


def manager_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return the loaded at entry."""
    return hass.config_entries.async_entries(DOMAIN)[0]


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


async def test_options_flow_shows_current_values(init_integration: MockConfigEntry, hass: HomeAssistant) -> None:
    """The options form starts from the defaults."""
    result = await hass.config_entries.options.async_init(init_integration.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    defaults = {str(key): key.default() for key in result["data_schema"].schema}
    assert defaults == {
        CONF_GRACE_MINUTES: DEFAULT_GRACE_MINUTES,
        CONF_HISTORY_DAYS: DEFAULT_HISTORY_DAYS,
        CONF_HISTORY_MAX: DEFAULT_HISTORY_MAX,
        CONF_PANEL_ADMIN_ONLY: DEFAULT_PANEL_ADMIN_ONLY,
        CONF_DEFER_RELATIVE: DEFAULT_DEFER_RELATIVE,
    }


@pytest.mark.parametrize("config_entry", [NEW_OPTIONS], indirect=True)
async def test_options_flow_shows_stored_values(init_integration: MockConfigEntry, hass: HomeAssistant) -> None:
    """Stored options are the form defaults."""
    result = await hass.config_entries.options.async_init(init_integration.entry_id)

    assert {str(key): key.default() for key in result["data_schema"].schema} == NEW_OPTIONS


async def test_options_flow_saves_values(init_integration: MockConfigEntry, hass: HomeAssistant) -> None:
    """Submitted options are stored in the entry and reach the reloaded manager."""
    result = await hass.config_entries.options.async_init(init_integration.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], NEW_OPTIONS)
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert init_integration.options == NEW_OPTIONS
    assert init_integration.state is ConfigEntryState.LOADED
    options = init_integration.runtime_data.manager._options  # noqa: SLF001
    assert options == ManagerOptions(grace=timedelta(minutes=10), history_days=3, history_max=20)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        (CONF_GRACE_MINUTES, -1),
        (CONF_GRACE_MINUTES, 1441),
        (CONF_HISTORY_DAYS, 0),
        (CONF_HISTORY_DAYS, 366),
        (CONF_HISTORY_MAX, 0),
        (CONF_HISTORY_MAX, 10001),
    ],
)
async def test_options_validation(init_integration: MockConfigEntry, hass: HomeAssistant, key: str, value: int) -> None:
    """Values outside the allowed ranges are rejected."""
    result = await hass.config_entries.options.async_init(init_integration.entry_id)

    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(result["flow_id"], {**NEW_OPTIONS, key: value})


@pytest.mark.parametrize(
    ("key", "value"), [(CONF_GRACE_MINUTES, 0), (CONF_GRACE_MINUTES, 1440), (CONF_HISTORY_DAYS, 365)]
)
async def test_options_validation_accepts_bounds(
    init_integration: MockConfigEntry, hass: HomeAssistant, key: str, value: int
) -> None:
    """The range limits themselves are allowed."""
    result = await hass.config_entries.options.async_init(init_integration.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {**NEW_OPTIONS, key: value})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][key] == value


async def test_options_reload_applies_panel_admin_only(init_integration: MockConfigEntry, hass: HomeAssistant) -> None:
    """The reload registers the panel again with the new admin-only setting."""
    with patch("custom_components.at.async_register_panel") as register:
        result = await hass.config_entries.options.async_init(init_integration.entry_id)
        await hass.config_entries.options.async_configure(result["flow_id"], NEW_OPTIONS)
        await hass.async_block_till_done()

    register.assert_awaited_once()
    assert register.await_args.args[1].options[CONF_PANEL_ADMIN_ONLY] is True


@pytest.mark.real_dependencies
@pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning")
async def test_options_reload_applies_defer_relative(hass: HomeAssistant, home: Assist, manager: JobManager) -> None:
    """Turning on defer-relative hands relative times back to Home Assistant after the reload."""
    entry = manager_entry(hass)
    await say(hass, home, "turn on the master bathroom light in 5 minutes")
    assert len(entry.runtime_data.manager.pending()) == 1

    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(result["flow_id"], NEW_OPTIONS)
    await hass.async_block_till_done()

    reloaded = entry.runtime_data.manager
    assert reloaded is not manager
    before = len(reloaded.pending())
    await say(hass, home, "turn on the master bathroom light in 5 minutes")
    assert len(reloaded.pending()) == before
