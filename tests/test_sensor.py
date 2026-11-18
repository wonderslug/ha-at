"""The next-job and pending-jobs sensors."""

from datetime import UTC, datetime, timedelta

from freezegun.api import FrozenDateTimeFactory
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.at.core.manager import JobManager
from custom_components.at.core.models import Job, JobKind, JobStatus, Result, Source, Targets, Via, new_job_id
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

NEXT = "sensor.at_next_job"
PENDING = "sensor.at_pending_jobs"
ACTION = [{"action": "light.turn_on", "target": {"entity_id": "light.porch"}}]


def make_job(due: datetime, summary: str) -> Job:
    return Job(
        id=new_job_id(),
        kind=JobKind.ACTION,
        status=JobStatus.PENDING,
        due=due,
        created_at=due,
        finished_at=None,
        summary=summary,
        original_text=None,
        intent=None,
        action=ACTION,
        raw_action=False,
        targets=Targets(),
        source=Source(via=Via.SERVICE),
        result=Result(),
    )


async def test_entity_ids(
    hass: HomeAssistant, init_integration: MockConfigEntry, entity_registry: er.EntityRegistry
) -> None:
    """The entity ids are exactly sensor.at_next_job and sensor.at_pending_jobs."""
    entry_id = init_integration.entry_id
    assert entity_registry.async_get_entity_id("sensor", "at", f"{entry_id}_next_job") == NEXT
    assert entity_registry.async_get_entity_id("sensor", "at", f"{entry_id}_pending_jobs") == PENDING


async def test_next_job_sensor_tracks_queue(
    hass: HomeAssistant, init_integration: MockConfigEntry, freezer: FrozenDateTimeFactory
) -> None:
    """Empty is unknown, then the earliest job, then the next one after a cancel."""
    manager: JobManager = init_integration.runtime_data.manager
    state = hass.states.get(NEXT)
    assert state is not None
    assert state.state == STATE_UNKNOWN
    assert state.attributes["job_id"] is None
    assert state.attributes["summary"] is None

    now = datetime.now(UTC).replace(microsecond=0)
    later = await manager.async_add(make_job(now + timedelta(days=2), "later"))
    soon = await manager.async_add(make_job(now + timedelta(hours=1), "soon"))
    await hass.async_block_till_done()
    state = hass.states.get(NEXT)
    assert state is not None
    assert state.state == (now + timedelta(hours=1)).isoformat()
    assert state.attributes["job_id"] == soon.id
    assert state.attributes["summary"] == "soon"

    await manager.async_cancel(soon.id, "test")
    await hass.async_block_till_done()
    state = hass.states.get(NEXT)
    assert state is not None
    assert state.state == (now + timedelta(days=2)).isoformat()
    assert state.attributes["job_id"] == later.id


async def test_pending_jobs_sensor_count_and_attributes(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """The count and the job list follow the queue."""
    manager: JobManager = init_integration.runtime_data.manager
    state = hass.states.get(PENDING)
    assert state is not None
    assert state.state == "0"
    assert state.attributes["jobs"] == []

    now = datetime.now(UTC).replace(microsecond=0)
    later = await manager.async_add(make_job(now + timedelta(days=2), "later"))
    soon = await manager.async_add(make_job(now + timedelta(hours=1), "soon"))
    await hass.async_block_till_done()
    state = hass.states.get(PENDING)
    assert state is not None
    assert state.state == "2"
    assert state.attributes["jobs"] == [
        {"id": soon.id, "due": soon.due.isoformat(), "summary": "soon"},
        {"id": later.id, "due": later.due.isoformat(), "summary": "later"},
    ]
