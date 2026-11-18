"""The to-do entity for the job queue."""

from datetime import UTC, datetime, timedelta

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.at.core.manager import JobManager
from custom_components.at.core.models import Job, JobKind, JobStatus, Result, Source, Targets, Via, new_job_id
from homeassistant.auth.models import User
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers import entity_registry as er
from tests.assist import ASSISTANT, Assist  # noqa: TID251  (plain module; see tests/assist.py)

pytestmark = [
    pytest.mark.real_dependencies,
    pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning"),
]

TODO = "todo.at_scheduled"
ACTION = [{"action": "light.turn_on", "target": {"entity_id": "light.porch"}}]


@pytest.fixture
async def manager(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    assist: Assist,
    entity_registry: er.EntityRegistry,
    config_entry: MockConfigEntry,
) -> JobManager:
    """Freeze now at 22:22 Chicago, expose a porch light, and load the integration."""
    await hass.config.async_set_time_zone("America/Chicago")
    freezer.move_to("2026-11-18 04:22:00+00:00")
    entry = entity_registry.async_get_or_create(
        "light", "test", "porch", suggested_object_id="porch", original_name="Porch Light"
    )
    hass.states.async_set(entry.entity_id, "off", {ATTR_FRIENDLY_NAME: "Porch Light"})
    async_expose_entity(hass, ASSISTANT, entry.entity_id, True)
    async_mock_service(hass, "light", "turn_on")
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry.runtime_data.manager


def make_job(
    due: datetime,
    *,
    status: JobStatus = JobStatus.PENDING,
    raw_action: bool = False,
    summary: str = "Turn on Porch Light",
    error: str | None = None,
    finished: datetime | None = None,
) -> Job:
    return Job(
        id=new_job_id(),
        kind=JobKind.ACTION,
        status=status,
        due=due,
        created_at=due,
        finished_at=None if status is JobStatus.PENDING else (finished or due),
        summary=summary,
        original_text=None,
        intent=None,
        action=ACTION,
        raw_action=raw_action,
        targets=Targets(),
        source=Source(via=Via.SERVICE),
        result=Result(error=error),
    )


async def items(hass: HomeAssistant) -> list[dict]:
    response = await hass.services.async_call(
        "todo", "get_items", {"entity_id": TODO}, blocking=True, return_response=True
    )
    return response[TODO]["items"]


async def todo_call(hass: HomeAssistant, service: str, data: dict, user: User | None = None) -> None:
    await hass.services.async_call(
        "todo",
        service,
        {"entity_id": TODO, **data},
        blocking=True,
        context=Context(user_id=user.id if user else None),
    )
    await hass.async_block_till_done()


async def test_entity_id(hass: HomeAssistant, manager: JobManager, entity_registry: er.EntityRegistry) -> None:
    """The entity id is exactly todo.at_scheduled."""
    entry_id = next(iter(hass.config_entries.async_entries("at"))).entry_id
    assert entity_registry.async_get_entity_id("todo", "at", f"{entry_id}_scheduled") == TODO


async def test_items_reflect_queue_and_history(hass: HomeAssistant, manager: JobManager) -> None:
    """Pending jobs come first by due time; history follows, newest first, with a description."""
    now = datetime.now(UTC).replace(microsecond=0)
    later = await manager.async_add(make_job(now + timedelta(days=2), summary="later"))
    soon = await manager.async_add(make_job(now + timedelta(hours=1), summary="soon"))
    done = make_job(now - timedelta(hours=5), status=JobStatus.DONE, summary="done")
    failed = make_job(
        now - timedelta(hours=4),
        status=JobStatus.FAILED,
        summary="failed",
        error="boom",
        finished=now - timedelta(hours=3),
    )
    missed = make_job(now - timedelta(hours=9), status=JobStatus.MISSED, summary="missed")
    cancelled = make_job(now - timedelta(hours=8), status=JobStatus.CANCELLED, summary="cancelled")
    for job in (done, failed, missed, cancelled):
        manager._jobs[job.id] = job  # noqa: SLF001
    manager._notify("added", done)  # noqa: SLF001
    await hass.async_block_till_done()

    got = await items(hass)
    assert [i["uid"] for i in got] == [soon.id, later.id, failed.id, done.id, cancelled.id, missed.id]
    assert [i["status"] for i in got] == ["needs_action"] * 2 + ["completed"] * 4
    assert got[0]["summary"] == "soon"
    assert datetime.fromisoformat(got[0]["due"]) == now + timedelta(hours=1)
    assert [i.get("description") for i in got[2:]] == ["Failed: boom", "Done", "Cancelled", "Missed"]


async def test_add_item_with_time_in_text(hass: HomeAssistant, manager: JobManager) -> None:
    """A time phrase in the summary schedules the recognized command."""
    await todo_call(hass, "add_item", {"item": "turn on the porch light at 11pm"})
    [job] = manager.pending()
    assert job.summary == "Turn on Porch Light"
    assert job.due == datetime(2026, 11, 18, 5, 0, tzinfo=UTC)
    assert job.source.via is Via.TODO


async def test_add_item_with_due_field(hass: HomeAssistant, manager: JobManager) -> None:
    """With no time phrase, the due field is the time."""
    await todo_call(hass, "add_item", {"item": "turn on the porch light", "due_datetime": "2026-11-18 23:30:00-06:00"})
    [job] = manager.pending()
    assert job.due == datetime(2026, 11, 19, 5, 30, tzinfo=UTC)


async def test_add_item_unrecognized_raises(hass: HomeAssistant, manager: JobManager) -> None:
    """A summary that can't be scheduled is a translated validation error."""
    with pytest.raises(ServiceValidationError) as err:
        await todo_call(hass, "add_item", {"item": "frobnicate the widget at 11pm"})
    assert "can only schedule commands" in str(err.value)
    assert manager.pending() == []


async def test_delete_pending_cancels(hass: HomeAssistant, manager: JobManager) -> None:
    """Removing a pending item cancels the job; removing a history item deletes it."""
    now = datetime.now(UTC)
    job = await manager.async_add(make_job(now + timedelta(hours=1)))
    old = make_job(now - timedelta(hours=1), status=JobStatus.DONE)
    manager._jobs[old.id] = old  # noqa: SLF001
    await todo_call(hass, "remove_item", {"item": job.id})
    assert manager.get(job.id).status is JobStatus.CANCELLED
    await todo_call(hass, "remove_item", {"item": old.id})
    assert old.id not in {j.id for j in manager.history()}


async def test_change_due_reschedules(hass: HomeAssistant, manager: JobManager) -> None:
    """Changing the due time of a pending item moves the job."""
    job = await manager.async_add(make_job(datetime.now(UTC) + timedelta(hours=1)))
    await todo_call(hass, "update_item", {"item": job.id, "due_datetime": "2026-11-19 08:00:00-06:00"})
    assert manager.get(job.id).due == datetime(2026, 11, 19, 14, 0, tzinfo=UTC)
    assert manager.get(job.id).status is JobStatus.PENDING


async def test_complete_pending_runs_now(hass: HomeAssistant, manager: JobManager) -> None:
    """Completing a pending item runs the job now."""
    job = await manager.async_add(make_job(datetime.now(UTC) + timedelta(hours=1)))
    await todo_call(hass, "update_item", {"item": job.id, "status": "completed"})
    await hass.async_block_till_done()
    assert manager.get(job.id).status is not JobStatus.PENDING


async def test_complete_raw_action_needs_admin(
    hass: HomeAssistant, manager: JobManager, hass_read_only_user: User, hass_admin_user: User
) -> None:
    """A non-admin can't run a raw action job from the list; an admin can."""
    job = await manager.async_add(make_job(datetime.now(UTC) + timedelta(hours=1), raw_action=True))
    with pytest.raises(Unauthorized):
        await todo_call(hass, "update_item", {"item": job.id, "status": "completed"}, hass_read_only_user)
    assert manager.get(job.id).status is JobStatus.PENDING
    await todo_call(hass, "update_item", {"item": job.id, "status": "completed"}, hass_admin_user)
    assert manager.get(job.id).status is not JobStatus.PENDING


async def test_summary_edit_rejected(hass: HomeAssistant, manager: JobManager) -> None:
    """The summary of a job can't be edited."""
    job = await manager.async_add(make_job(datetime.now(UTC) + timedelta(hours=1)))
    with pytest.raises(ServiceValidationError, match="Cancel and re-add"):
        await todo_call(hass, "update_item", {"item": job.id, "rename": "something else"})
    assert manager.get(job.id).summary == "Turn on Porch Light"


async def test_stale_item_is_a_validation_error(hass: HomeAssistant, manager: JobManager) -> None:
    """A job that finished before the update arrives is reported, not crashed on."""
    job = await manager.async_add(make_job(datetime.now(UTC) + timedelta(hours=1)))
    await manager.async_cancel(job.id, "test")
    with pytest.raises(ServiceValidationError, match="not waiting"):
        await todo_call(hass, "update_item", {"item": job.id, "due_datetime": "2026-11-19 08:00:00-06:00"})
