"""Tests for the diagnostics download."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.at.core.models import Job, JobKind, JobStatus, Result, Source, Targets, Via
from custom_components.at.diagnostics import async_get_config_entry_diagnostics
from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

ADAPTERS = {"recognize", "intents", "sentence_triggers", "fallthrough"}


async def test_diagnostics_contents(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Diagnostics hold the options, status counts, language support and adapter probes, minus user ids."""
    hass.config_entries.async_update_entry(
        init_integration, options={**init_integration.options, "user_id": "opt-user-1"}
    )
    now = dt_util.utcnow()
    manager = init_integration.runtime_data.manager
    await manager.async_add(
        Job(
            id="job1",
            kind=JobKind.ACTION,
            status=JobStatus.PENDING,
            due=now.replace(year=now.year + 1),
            created_at=now,
            finished_at=None,
            summary="Secret summary",
            original_text="secret words",
            intent=None,
            action=[{"action": "light.turn_on"}],
            raw_action=False,
            targets=Targets(),
            source=Source(via=Via.SERVICE, user_id="user-abc-123"),
            result=Result(),
        )
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)

    assert diagnostics["entry"]["options"] == {**init_integration.options, "user_id": REDACTED}
    assert diagnostics["counts"]["pending"] == 1
    assert set(diagnostics["counts"]) == {str(status) for status in JobStatus}
    assert diagnostics["language_supported"] is True
    probes = diagnostics["ha_internal"]
    assert set(probes) == ADAPTERS
    assert all(isinstance(ok, bool) for adapter in probes.values() for ok in adapter.values())
    assert all(ok for adapter in probes.values() for ok in adapter.values())
    text = str(diagnostics)
    assert "user-abc-123" not in text
    assert "opt-user-1" not in text
    assert "Secret summary" not in text
    assert "secret words" not in text
