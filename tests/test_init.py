"""Tests for setting up and unloading the entry."""

from datetime import timedelta
from typing import Any

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.at.const import DISPLAY_NAME, DOMAIN, STORAGE_KEY
from custom_components.at.core.models import Job, JobKind, JobStatus, Result, Source, Targets, Via
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util


async def test_setup_and_unload_entry(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """The entry sets up and unloads cleanly."""
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_remove_entry_deletes_stored_jobs(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_storage: dict[str, Any]
) -> None:
    """Removing the integration deletes the job store, and a new setup starts empty."""
    now = dt_util.utcnow()
    manager = init_integration.runtime_data.manager
    await manager.async_add(
        Job(
            id="job1",
            kind=JobKind.ACTION,
            status=JobStatus.PENDING,
            due=now + timedelta(days=1),
            created_at=now,
            finished_at=None,
            summary="Later",
            original_text=None,
            intent=None,
            action=[{"action": "light.turn_on"}],
            raw_action=False,
            targets=Targets(),
            source=Source(via=Via.SERVICE),
            result=Result(),
        )
    )
    assert STORAGE_KEY in hass_storage

    await hass.config_entries.async_remove(init_integration.entry_id)
    await hass.async_block_till_done()
    assert STORAGE_KEY not in hass_storage

    fresh = MockConfigEntry(domain=DOMAIN, title=DISPLAY_NAME, data={})
    fresh.add_to_hass(hass)
    await hass.config_entries.async_setup(fresh.entry_id)
    await hass.async_block_till_done()
    assert fresh.runtime_data.manager.pending() == []
