"""Tests for resolving the automation or script behind a call."""

from custom_components.at.core.context import origin_entity_id
from homeassistant.core import Context, HomeAssistant


async def test_matches_automation_run_context(hass: HomeAssistant) -> None:
    run = Context()
    hass.states.async_set("automation.bedtime", "on", context=run)
    hass.states.async_set("automation.other", "on", context=Context())
    assert origin_entity_id(hass, run) == "automation.bedtime"


async def test_matches_script_run_context(hass: HomeAssistant) -> None:
    run = Context()
    hass.states.async_set("script.tidy_up", "on", context=run)
    assert origin_entity_id(hass, run) == "script.tidy_up"


async def test_ignores_other_domains(hass: HomeAssistant) -> None:
    run = Context()
    hass.states.async_set("light.porch", "on", context=run)
    assert origin_entity_id(hass, run) is None


async def test_no_context(hass: HomeAssistant) -> None:
    assert origin_entity_id(hass, None) is None


async def test_prefers_script_called_by_automation(hass: HomeAssistant) -> None:
    run = Context()
    hass.states.async_set("automation.bedtime", "on", context=run)
    hass.states.async_set("script.tidy_up", "on", context=run)
    assert origin_entity_id(hass, run) == "script.tidy_up"
