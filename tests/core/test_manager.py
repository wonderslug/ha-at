"""Tests for the job manager."""

import asyncio
from collections.abc import AsyncGenerator, Callable, Coroutine
import dataclasses
from datetime import timedelta
from typing import Any
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import async_capture_events, async_fire_time_changed

from custom_components.at.const import SWEEP_INTERVAL
from custom_components.at.core.errors import JobExecutionError, JobStateError
from custom_components.at.core.manager import JobChange, JobManager, ManagerOptions
from custom_components.at.core.models import Job, JobKind, JobStatus, Result, Source, Targets, Via, new_job_id
from custom_components.at.core.store import JobStore
from homeassistant.core import Context, HomeAssistant
from homeassistant.util import dt as dt_util

PAYLOAD_KEYS = {"job_id", "summary", "due", "status", "via"}


class FakeExecutor:
    """Record executed jobs, optionally raising."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.error: str | None = None
        self.crash: Exception | None = None
        self.block: asyncio.Event | None = None

    async def async_execute(self, job: Job) -> None:
        self.calls.append(job.id)
        if self.block is not None:
            await self.block.wait()
        if self.crash is not None:
            raise self.crash
        if self.error is not None:
            raise JobExecutionError(self.error)


def _job(due_in: timedelta = timedelta(minutes=10), summary: str = "turn on the light") -> Job:
    now = dt_util.utcnow()
    return Job(
        id=new_job_id(),
        kind=JobKind.ACTION,
        status=JobStatus.PENDING,
        due=now + due_in,
        created_at=now,
        finished_at=None,
        summary=summary,
        original_text=None,
        intent=None,
        action=[{"action": "light.turn_on", "target": {"entity_id": "light.kitchen"}}],
        raw_action=False,
        targets=Targets(entity_ids=["light.kitchen"]),
        source=Source(via=Via.SERVICE),
        result=Result(),
    )


type MakeManager = Callable[..., Coroutine[Any, Any, JobManager]]


@pytest.fixture
def executor() -> FakeExecutor:
    return FakeExecutor()


@pytest.fixture
async def make_manager(
    hass: HomeAssistant, hass_storage: dict[str, Any], executor: FakeExecutor
) -> AsyncGenerator[MakeManager]:
    managers: list[JobManager] = []

    async def _make(**options: Any) -> JobManager:
        opts = ManagerOptions(
            grace=options.get("grace", timedelta(minutes=5)),
            history_days=options.get("history_days", 7),
            history_max=options.get("history_max", 100),
        )
        manager = JobManager(hass, JobStore(hass), executor, opts)
        managers.append(manager)
        await manager.async_start()
        return manager

    yield _make
    for manager in managers:
        await manager.async_stop()


async def _advance(hass: HomeAssistant, freezer: FrozenDateTimeFactory, delta: timedelta) -> None:
    freezer.tick(delta)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)


async def test_add_fires_at_due_time(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    scheduled = async_capture_events(hass, "at_job_scheduled")
    executed = async_capture_events(hass, "at_job_executed")
    manager = await make_manager()
    job = await manager.async_add(_job())

    await _advance(hass, freezer, timedelta(minutes=9))
    assert executor.calls == []

    await _advance(hass, freezer, timedelta(minutes=1))
    assert executor.calls == [job.id]
    stored = manager.get(job.id)
    assert stored.status is JobStatus.DONE
    assert stored.finished_at is not None
    assert len(scheduled) == 1
    assert len(executed) == 1
    assert set(scheduled[0].data) == PAYLOAD_KEYS
    assert set(executed[0].data) == PAYLOAD_KEYS
    assert executed[0].data["job_id"] == job.id
    assert executed[0].data["status"] == "done"
    assert executed[0].data["via"] == "service"
    assert executed[0].data["due"] == job.due.isoformat()


async def test_executor_error_marks_failed(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    failed = async_capture_events(hass, "at_job_failed")
    executor.error = "boom"
    manager = await make_manager()
    job = await manager.async_add(_job())

    await _advance(hass, freezer, timedelta(minutes=10))
    stored = manager.get(job.id)
    assert stored.status is JobStatus.FAILED
    assert stored.result.error == "boom"
    assert stored.finished_at is not None
    assert len(failed) == 1
    assert set(failed[0].data) == PAYLOAD_KEYS | {"error"}
    assert failed[0].data["error"] == "boom"


async def test_cancel_records_who_and_where(hass: HomeAssistant, make_manager: MakeManager) -> None:
    cancelled = async_capture_events(hass, "at_job_cancelled")
    manager = await make_manager()
    first = await manager.async_add(_job())
    second = await manager.async_add(_job())
    run = Context(user_id="user-7")
    hass.states.async_set("automation.bedtime", "on", context=run)

    await manager.async_cancel(first.id, by="service", context=run, device_id="sat-1")
    [other] = await manager.async_cancel_many([second.id], by="panel", context=Context(user_id="user-8"))

    assert first.result.cancelled_user_id == "user-7"
    assert first.result.cancelled_origin == "automation.bedtime"
    assert other.result.cancelled_user_id == "user-8"
    assert other.result.cancelled_origin is None
    assert first.result.cancelled_device_id == "sat-1"
    assert other.result.cancelled_device_id is None
    await hass.async_block_till_done(wait_background_tasks=True)
    assert cancelled[0].context.id == run.id
    assert cancelled[1].context.user_id == "user-8"


async def test_cancel_pending(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    cancelled = async_capture_events(hass, "at_job_cancelled")
    manager = await make_manager()
    job = await manager.async_add(_job())

    result = await manager.async_cancel(job.id, by="user-1")
    assert result.status is JobStatus.CANCELLED
    assert result.result.cancelled_by == "user-1"
    assert result.finished_at is not None
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(cancelled) == 1

    await _advance(hass, freezer, timedelta(minutes=11))
    assert executor.calls == []

    with pytest.raises(JobStateError):
        await manager.async_cancel(job.id, by="user-1")


async def test_set_due_reschedules(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    manager = await make_manager()
    job = await manager.async_add(_job())
    await manager.async_set_due(job.id, dt_util.utcnow() + timedelta(minutes=20))

    await _advance(hass, freezer, timedelta(minutes=10, seconds=30))
    assert executor.calls == []
    assert manager.get(job.id).status is JobStatus.PENDING

    await _advance(hass, freezer, timedelta(minutes=10))
    assert executor.calls == [job.id]
    assert manager.get(job.id).status is JobStatus.DONE


async def test_run_now(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    manager = await make_manager()
    job = await manager.async_add(_job())

    await manager.async_run_now(job.id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert executor.calls == [job.id]
    assert manager.get(job.id).status is JobStatus.DONE

    await _advance(hass, freezer, timedelta(minutes=11))
    assert executor.calls == [job.id]


async def test_reschedule_raw_action_override(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    manager = await make_manager()
    job = await manager.async_add(_job())
    new_due = dt_util.utcnow() + timedelta(hours=1)

    kept = await manager.async_reschedule(job.id, new_due)
    flagged = await manager.async_reschedule(job.id, new_due, raw_action=True)

    assert kept.raw_action is False
    assert flagged.raw_action is True
    assert (await manager.async_reschedule(flagged.id, new_due)).raw_action is True


async def test_reschedule_copies_history_job(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    manager = await make_manager()
    job = await manager.async_add(_job())
    await _advance(hass, freezer, timedelta(minutes=10))
    original = dataclasses.replace(manager.get(job.id))

    new_due = dt_util.utcnow() + timedelta(hours=1)
    copy = await manager.async_reschedule(job.id, new_due)

    assert copy.id != job.id
    assert copy.status is JobStatus.PENDING
    assert copy.due == new_due
    assert copy.summary == job.summary
    assert copy.action == job.action
    assert copy.finished_at is None
    assert copy.result == Result()
    assert manager.get(job.id) == original
    assert manager.get(job.id).status is JobStatus.DONE
    assert [j.id for j in manager.pending()] == [copy.id]


async def test_sweep_fires_overdue_after_clock_jump(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    manager = await make_manager()
    job = await manager.async_add(_job(timedelta(minutes=5)))

    freezer.move_to(dt_util.utcnow() + timedelta(minutes=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    await _advance(hass, freezer, timedelta(minutes=1))

    assert executor.calls == [job.id]
    assert manager.get(job.id).status is JobStatus.DONE


async def test_restart_restores_pending(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    first = await make_manager()
    job = await first.async_add(_job())
    await first.async_stop()

    second = await make_manager()
    assert [j.id for j in second.pending()] == [job.id]

    await _advance(hass, freezer, timedelta(minutes=10))
    assert executor.calls == [job.id]
    assert second.get(job.id).status is JobStatus.DONE


async def _seed(hass: HomeAssistant, *jobs: Job) -> None:
    await JobStore(hass).async_save(list(jobs))


async def test_restart_within_grace_runs_now(
    hass: HomeAssistant, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    job = _job(-timedelta(minutes=3))
    await _seed(hass, job)
    executed = async_capture_events(hass, "at_job_executed")

    manager = await make_manager(grace=timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)

    assert executor.calls == [job.id]
    assert manager.get(job.id).status is JobStatus.DONE
    assert manager.get(job.id).finished_at is not None
    assert len(executed) == 1


async def test_restart_beyond_grace_marks_missed(
    hass: HomeAssistant, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    job = _job(-timedelta(minutes=10))
    await _seed(hass, job)
    missed = async_capture_events(hass, "at_job_missed")

    manager = await make_manager(grace=timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)

    assert executor.calls == []
    stored = manager.get(job.id)
    assert stored.status is JobStatus.MISSED
    assert stored.finished_at is not None
    assert len(missed) == 1
    assert set(missed[0].data) == PAYLOAD_KEYS

    reloaded = {j.id: j for j in await JobStore(hass).async_load()}
    assert reloaded[job.id].status is JobStatus.MISSED


async def test_running_job_at_startup_becomes_failed(
    hass: HomeAssistant, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    job = _job(-timedelta(minutes=1))
    job.status = JobStatus.RUNNING
    await _seed(hass, job)

    manager = await make_manager()
    await hass.async_block_till_done(wait_background_tasks=True)

    stored = manager.get(job.id)
    assert stored.status is JobStatus.FAILED
    assert stored.result.error == "Interrupted by restart"
    assert stored.finished_at is not None
    assert executor.calls == []


async def test_two_jobs_same_instant_both_run(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    manager = await make_manager()
    first = await manager.async_add(_job())
    second = await manager.async_add(dataclasses.replace(_job(), due=first.due))

    await _advance(hass, freezer, timedelta(minutes=10))
    assert sorted(executor.calls) == sorted([first.id, second.id])
    assert manager.get(first.id).status is JobStatus.DONE
    assert manager.get(second.id).status is JobStatus.DONE


async def test_history_pruned_after_finish(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    manager = await make_manager(history_max=2)
    for minutes in (1, 2, 3):
        await manager.async_add(_job(timedelta(minutes=minutes)))
    for _ in range(3):
        await _advance(hass, freezer, timedelta(minutes=1))

    assert len(executor.calls) == 3
    history = manager.history()
    assert len(history) == 2
    assert [j.id for j in history] == executor.calls[:0:-1]
    reloaded = await JobStore(hass).async_load()
    assert len(reloaded) == 2


async def test_stop_runs_every_callback_even_if_one_raises(
    hass: HomeAssistant, make_manager: MakeManager, caplog: pytest.LogCaptureFixture
) -> None:
    manager = await make_manager()
    stopped: list[str] = []

    def failing() -> None:
        msg = "boom"
        raise RuntimeError(msg)

    manager.subscribe(lambda change: None, on_stop=failing)
    manager.subscribe(lambda change: None, on_stop=lambda: stopped.append("second"))

    await manager.async_stop()

    assert stopped == ["second"]
    assert "A stop callback raised an error" in caplog.text
    assert manager._subscribers == []  # noqa: SLF001 - stop must still drop every subscriber


async def test_subscribe_receives_changes(hass: HomeAssistant, make_manager: MakeManager) -> None:
    manager = await make_manager()
    changes: list[JobChange] = []
    unsub = manager.subscribe(changes.append)

    job = await manager.async_add(_job())
    await manager.async_cancel(job.id, by="user-1")
    assert [(c.kind, c.job.id) for c in changes] == [("added", job.id), ("updated", job.id)]

    unsub()
    await manager.async_add(_job())
    assert len(changes) == 2


async def test_sweep_alone_launches_overdue_job_once(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    """With no per-job timer at all, the sweep is what runs the job."""
    with patch(
        "custom_components.at.core.manager.async_track_point_in_utc_time",
        return_value=lambda: None,
    ) as track:
        manager = await make_manager()
        job = await manager.async_add(_job(timedelta(seconds=30)))
        assert track.call_count == 1

        await _advance(hass, freezer, timedelta(seconds=30))
        assert executor.calls == []

        await _advance(hass, freezer, SWEEP_INTERVAL)
        assert executor.calls == [job.id]
        assert manager.get(job.id).status is JobStatus.DONE

        await _advance(hass, freezer, SWEEP_INTERVAL)
        assert executor.calls == [job.id]


async def test_unexpected_executor_error_marks_failed(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    failed = async_capture_events(hass, "at_job_failed")
    executor.crash = RuntimeError("kaboom")
    manager = await make_manager()
    job = await manager.async_add(_job())

    await _advance(hass, freezer, timedelta(minutes=10))
    stored = manager.get(job.id)
    assert stored.status is JobStatus.FAILED
    assert stored.result.error == "kaboom"
    assert stored.finished_at is not None
    assert len(failed) == 1
    assert failed[0].data["job_id"] == job.id


async def test_failed_running_save_still_marks_failed(
    hass: HomeAssistant, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    manager = await make_manager()
    job = await manager.async_add(_job())
    failed = async_capture_events(hass, "at_job_failed")

    with patch.object(JobStore, "async_save", side_effect=[OSError("disk full"), None]):
        await manager.async_run_now(job.id)
        await hass.async_block_till_done(wait_background_tasks=True)

    assert executor.calls == []
    stored = manager.get(job.id)
    assert stored.status is JobStatus.FAILED
    assert stored.result.error == "disk full"
    assert stored.finished_at is not None
    assert len(failed) == 1


async def test_running_job_rejects_changes_and_survives_stop_as_running(
    hass: HomeAssistant, make_manager: MakeManager, executor: FakeExecutor
) -> None:
    executor.block = asyncio.Event()
    manager = await make_manager()
    job = await manager.async_add(_job())

    await manager.async_run_now(job.id)
    await hass.async_block_till_done()
    assert executor.calls == [job.id]
    assert [j.id for j in manager.running()] == [job.id]
    assert manager.pending() == []

    with pytest.raises(JobStateError):
        await manager.async_run_now(job.id)
    with pytest.raises(JobStateError):
        await manager.async_cancel(job.id, by="user-1")

    await manager.async_stop()
    stored = {j.id: j for j in await JobStore(hass).async_load()}
    assert stored[job.id].status is JobStatus.RUNNING

    executor.block = None
    restarted = await make_manager()
    recovered = restarted.get(job.id)
    assert recovered.status is JobStatus.FAILED
    assert recovered.result.error == "Interrupted by restart"
    assert recovered.finished_at is not None
    assert executor.calls == [job.id]


async def test_add_rolls_back_when_save_fails(hass: HomeAssistant, make_manager: MakeManager) -> None:
    """A failed save leaves the job set as it was, and later adds still work."""
    manager = await make_manager()
    events = async_capture_events(hass, "at_job_scheduled")
    failed = _job()
    with (
        patch.object(JobStore, "async_save", side_effect=TypeError("not JSON serializable")),
        pytest.raises(TypeError),
    ):
        await manager.async_add(failed)
    assert manager.pending() == []
    assert events == []

    added = await manager.async_add(_job())
    assert [job.id for job in manager.pending()] == [added.id]


class GatedSave:
    """Hold the ``nth`` store save open until released; every other save goes through."""

    def __init__(self, nth: int) -> None:
        self.nth = nth
        self.calls = 0
        self.reached = asyncio.Event()
        self.release = asyncio.Event()
        self._real = JobStore.async_save

    def patch(self) -> Any:
        """Return a patch that routes every ``JobStore.async_save`` through this gate."""

        async def _save(store: JobStore, jobs: Any) -> None:
            self.calls += 1
            if self.calls == self.nth:
                self.reached.set()
                await self.release.wait()
            await self._real(store, jobs)

        return patch.object(JobStore, "async_save", _save)

    async def wait_reached(self) -> None:
        """Wait until the gated save has started."""
        async with asyncio.timeout(5):
            await self.reached.wait()


async def test_stop_during_finish_save_records_done(hass: HomeAssistant, make_manager: MakeManager) -> None:
    """A job that ran is stored as done even when stopping cuts off its final save."""
    manager = await make_manager()
    job = await manager.async_add(_job())
    gate = GatedSave(nth=2)

    with gate.patch():
        await manager.async_run_now(job.id)
        await gate.wait_reached()
        await manager.async_stop()

    stored = {j.id: j for j in await JobStore(hass).async_load()}
    assert stored[job.id].status is JobStatus.DONE


async def test_cancel_while_add_is_saving(
    hass: HomeAssistant, make_manager: MakeManager, executor: FakeExecutor, freezer: FrozenDateTimeFactory
) -> None:
    """Cancelling a job whose add is still saving sends no scheduled event and never runs it."""
    manager = await make_manager()
    scheduled = async_capture_events(hass, "at_job_scheduled")
    cancelled = async_capture_events(hass, "at_job_cancelled")
    job = _job(due_in=timedelta(minutes=1))
    gate = GatedSave(nth=1)

    with gate.patch():
        adding = hass.async_create_task(manager.async_add(job))
        await gate.wait_reached()
        await manager.async_cancel(job.id, by="user-1")
        gate.release.set()
        await adding

    await _advance(hass, freezer, timedelta(minutes=2))
    assert scheduled == []
    assert len(cancelled) == 1
    assert manager.get(job.id).status is JobStatus.CANCELLED
    assert executor.calls == []


async def test_run_now_while_add_is_saving_raises(
    hass: HomeAssistant, make_manager: MakeManager, executor: FakeExecutor, freezer: FrozenDateTimeFactory
) -> None:
    """Run now during the add's save is refused, and the job still runs at its due time."""
    manager = await make_manager()
    job = _job(due_in=timedelta(minutes=1))
    gate = GatedSave(nth=1)

    with gate.patch():
        adding = hass.async_create_task(manager.async_add(job))
        await gate.wait_reached()
        with pytest.raises(JobStateError):
            await manager.async_run_now(job.id)
        gate.release.set()
        await adding

    assert executor.calls == []
    await _advance(hass, freezer, timedelta(minutes=2))
    assert executor.calls == [job.id]
    assert manager.get(job.id).status is JobStatus.DONE
