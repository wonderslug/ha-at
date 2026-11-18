"""Sentence triggers when Home Assistant's conversation internals are missing."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.at.ha_internal import sentence_triggers
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant


@pytest.mark.parametrize("name", ["get_agent_manager", "AgentManager", "IntentSource"])
async def test_setup_without_conversation_internals(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    name: str,
) -> None:
    """Without the agent manager the sentences are skipped with a warning, and setup succeeds."""
    monkeypatch.setattr(sentence_triggers, name, None)
    assert not all(sentence_triggers.probe().values())

    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    assert "conversation agent manager" in caplog.text
    assert await hass.config_entries.async_unload(config_entry.entry_id)
