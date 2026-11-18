"""Tests for the job executor."""

from datetime import UTC, datetime
from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.at.core.errors import JobExecutionError
from custom_components.at.core.executor import JobExecutor
from custom_components.at.core.models import IntentSpec, Job, JobKind, JobStatus, Result, Source, Targets, Via
from homeassistant.auth.models import User
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from tests.conftest import Assist  # noqa: TID251  (shared fixture's result type)

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)


def make_job(
    *,
    action: list[dict[str, Any]] | None = None,
    intent: IntentSpec | None = None,
    user_id: str | None = None,
) -> Job:
    """Build a pending job of either kind."""
    return Job(
        id="abc12345",
        kind=JobKind.INTENT if intent else JobKind.ACTION,
        status=JobStatus.RUNNING,
        due=NOW,
        created_at=NOW,
        finished_at=None,
        summary="test",
        original_text=None,
        intent=intent,
        action=action,
        raw_action=False,
        targets=Targets(),
        source=Source(via=Via.SERVICE, user_id=user_id),
        result=Result(),
    )


def turn_on(entity_id: str) -> list[dict[str, Any]]:
    """Build a one-step turn-on action."""
    return [{"action": "light.turn_on", "target": {"entity_id": entity_id}}]


async def test_action_job_runs_service(hass: HomeAssistant) -> None:
    """An action job calls its service."""
    hass.states.async_set("light.porch", "off")
    calls = async_mock_service(hass, "light", "turn_on")
    await JobExecutor(hass).async_execute(make_job(action=turn_on("light.porch")))
    assert [call.data["entity_id"] for call in calls] == [["light.porch"]]


async def test_script_job_passes_variables(hass: HomeAssistant) -> None:
    """script.turn_on hands the stored variables to the script."""
    assert await async_setup_component(hass, "input_text", {"input_text": {"x": {}}})
    assert await async_setup_component(
        hass,
        "script",
        {
            "script": {
                "say": {
                    "sequence": [
                        {
                            "action": "input_text.set_value",
                            "target": {"entity_id": "input_text.x"},
                            "data": {"value": "{{ msg }}"},
                        }
                    ]
                }
            }
        },
    )
    action = [
        {
            "action": "script.turn_on",
            "target": {"entity_id": "script.say"},
            "data": {"variables": {"msg": "hi"}},
        }
    ]
    await JobExecutor(hass).async_execute(make_job(action=action))
    await hass.async_block_till_done()
    assert hass.states.get("input_text.x").state == "hi"  # type: ignore[union-attr]


async def test_automation_trigger_job(hass: HomeAssistant) -> None:
    """automation.trigger runs the automation's actions."""
    calls = async_mock_service(hass, "test", "hit")
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "alias": "Morning",
                "triggers": {"trigger": "event", "event_type": "never"},
                "actions": {"action": "test.hit"},
            }
        },
    )
    action = [{"action": "automation.trigger", "target": {"entity_id": "automation.morning"}}]
    await JobExecutor(hass).async_execute(make_job(action=action))
    await hass.async_block_till_done()
    assert len(calls) == 1


async def test_deleted_target_fails_cleanly(hass: HomeAssistant) -> None:
    """A script that no longer exists gives a readable failure, not a silent no-op."""
    assert await async_setup_component(hass, "script", {"script": {}})
    action = [{"action": "script.turn_on", "target": {"entity_id": "script.gone"}}]
    with pytest.raises(JobExecutionError, match=r"script\.gone"):
        await JobExecutor(hass).async_execute(make_job(action=action))


async def test_missing_service_fails_cleanly(hass: HomeAssistant) -> None:
    """A service that is gone is named in the error."""
    hass.states.async_set("light.porch", "off")
    with pytest.raises(JobExecutionError, match=r"light\.turn_on"):
        await JobExecutor(hass).async_execute(make_job(action=turn_on("light.porch")))


async def test_context_user_missing_falls_back_to_system(hass: HomeAssistant, hass_admin_user: User) -> None:
    """The job's user is used when it still exists; otherwise the context has no user."""
    hass.states.async_set("light.porch", "off")
    calls = async_mock_service(hass, "light", "turn_on")
    executor = JobExecutor(hass)
    await executor.async_execute(make_job(action=turn_on("light.porch"), user_id=hass_admin_user.id))
    await executor.async_execute(make_job(action=turn_on("light.porch"), user_id="deleted-user"))
    await executor.async_execute(make_job(action=turn_on("light.porch")))
    assert [call.context.user_id for call in calls] == [hass_admin_user.id, None, None]


@pytest.mark.real_dependencies
@pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning")
async def test_intent_job_runs_and_rechecks_exposure(hass: HomeAssistant, assist: Assist) -> None:
    """A stored intent runs; once the target is un-exposed the same job fails."""
    spec = IntentSpec(
        type="HassTurnOn",
        slots={"name": {"value": "Kitchen light", "text": "kitchen light"}},
        language="en",
        device_id=assist.device_id,
    )
    executor = JobExecutor(hass)
    await executor.async_execute(make_job(intent=spec))
    assert [call.data["entity_id"] for call in assist.turn_on_calls] == [["light.kitchen"]]

    async_expose_entity(hass, "conversation", "light.kitchen", False)
    with pytest.raises(JobExecutionError, match="Kitchen light"):
        await executor.async_execute(make_job(intent=spec))
    assert len(assist.turn_on_calls) == 1


@pytest.mark.real_dependencies
@pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning")
async def test_unknown_intent_fails_cleanly(hass: HomeAssistant, assist: Assist) -> None:
    """An intent type that no longer exists becomes a JobExecutionError."""
    spec = IntentSpec(type="HassGone", slots={}, language="en", device_id=assist.device_id)
    with pytest.raises(JobExecutionError, match="HassGone"):
        await JobExecutor(hass).async_execute(make_job(intent=spec))
