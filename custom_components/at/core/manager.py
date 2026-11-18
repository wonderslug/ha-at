"""Job queue: per-job timers, a once-a-minute sweep, restart recovery and events."""

import asyncio
from collections.abc import Callable
import copy
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal, Protocol

from custom_components.at.const import (
    EVENT_JOB_CANCELLED,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_FAILED,
    EVENT_JOB_MISSED,
    EVENT_JOB_SCHEDULED,
    LOGGER,
    SWEEP_INTERVAL,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_utc_time, async_track_time_interval
from homeassistant.util import dt as dt_util

from .errors import JobExecutionError, JobNotFound, JobStateError
from .events import fire_job_event
from .models import Job, JobStatus, Result, new_job_id
from .store import HISTORY_STATUSES, prune_history

if TYPE_CHECKING:
    from .store import JobStore

INTERRUPTED_ERROR = "Interrupted by restart"

_FINISH_EVENTS = {
    JobStatus.CANCELLED: EVENT_JOB_CANCELLED,
    JobStatus.DONE: EVENT_JOB_EXECUTED,
    JobStatus.FAILED: EVENT_JOB_FAILED,
    JobStatus.MISSED: EVENT_JOB_MISSED,
}


@dataclass
class ManagerOptions:
    """Tunable manager settings."""

    grace: timedelta
    history_days: int
    history_max: int


@dataclass
class JobChange:
    """A change to the job set, passed to subscribers."""

    kind: Literal["added", "updated", "removed"]
    job: Job


class Executor(Protocol):
    """Runs a due job."""

    async def async_execute(self, job: Job) -> None:
        """Run the job; raise ``JobExecutionError`` on failure."""


class JobManager:
    """Own every job and decide when each one runs."""

    def __init__(
        self,
        hass: HomeAssistant,
        store: JobStore,
        executor: Executor,
        options: ManagerOptions,
    ) -> None:
        """Initialise an empty, stopped manager."""
        self._hass = hass
        self._store = store
        self._executor = executor
        self._options = options
        self._jobs: dict[str, Job] = {}
        self._timers: dict[str, CALLBACK_TYPE] = {}
        self._in_flight: set[str] = set()
        self._settling: set[str] = set()
        self._tasks: set[asyncio.Task[None]] = set()
        self._subscribers: list[Callable[[JobChange], None]] = []
        self._unsub_sweep: CALLBACK_TYPE | None = None

    # Lifecycle

    async def async_start(self) -> None:
        """Load stored jobs, recover after a restart, and start the timers."""
        now = dt_util.utcnow()
        self._jobs = {job.id: job for job in await self._store.async_load()}
        finished: list[Job] = []
        overdue: list[str] = []
        for job in self._jobs.values():
            if job.status is JobStatus.RUNNING:
                job.status = JobStatus.FAILED
                job.result.error = INTERRUPTED_ERROR
                job.finished_at = now
                finished.append(job)
            elif job.status is JobStatus.PENDING:
                if job.due > now:
                    self._schedule(job)
                elif now - job.due <= self._options.grace:
                    overdue.append(job.id)
                else:
                    job.status = JobStatus.MISSED
                    job.finished_at = now
                    finished.append(job)
        self._prune()
        await self._async_save()
        for job in finished:
            fire_job_event(self._hass, _FINISH_EVENTS[job.status], job)
        self._unsub_sweep = async_track_time_interval(self._hass, self._sweep, SWEEP_INTERVAL)
        for job_id in overdue:
            self._launch(job_id)

    async def async_stop(self) -> None:
        """Cancel timers, the sweep and running tasks; running jobs stay running in storage."""
        if self._unsub_sweep is not None:
            self._unsub_sweep()
            self._unsub_sweep = None
        for unsub in self._timers.values():
            unsub()
        self._timers.clear()
        tasks = list(self._tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
        self._in_flight.clear()

    # Reads

    def get(self, job_id: str) -> Job:
        """Return the job with this id."""
        try:
            return self._jobs[job_id]
        except KeyError:
            raise JobNotFound(f"No job with id {job_id}") from None

    def pending(self) -> list[Job]:
        """Return pending jobs, soonest first."""
        return self._by_status(JobStatus.PENDING)

    def running(self) -> list[Job]:
        """Return jobs that are running now, soonest due first."""
        return self._by_status(JobStatus.RUNNING)

    def _by_status(self, status: JobStatus) -> list[Job]:
        return sorted((j for j in self._jobs.values() if j.status is status), key=lambda j: j.due)

    def history(self) -> list[Job]:
        """Return finished jobs, newest first."""
        done = [j for j in self._jobs.values() if j.status in HISTORY_STATUSES]
        return sorted(done, key=lambda j: j.finished_at or j.due, reverse=True)

    # Queue changes

    async def async_add(self, job: Job) -> Job:
        """Queue a job and schedule it."""
        while job.id in self._jobs:
            job.id = new_job_id()
        job.status = JobStatus.PENDING
        job.finished_at = None
        self._jobs[job.id] = job
        await self._async_announce(job, "added")
        return job

    async def async_cancel(self, job_id: str, by: str) -> Job:
        """Cancel a pending job."""
        job = self._require_pending(job_id)
        self._cancel(job, by)
        await self._async_after_finish([job])
        return job

    async def async_cancel_many(self, job_ids: list[str], by: str) -> list[Job]:
        """Cancel several pending jobs; nothing changes if any of them is not pending."""
        jobs = [self._require_pending(job_id) for job_id in dict.fromkeys(job_ids)]
        for job in jobs:
            self._cancel(job, by)
        await self._async_after_finish(jobs)
        return jobs

    async def async_set_due(self, job_id: str, due: datetime) -> Job:
        """Move a pending job to a new due time."""
        job = self._require_pending(job_id)
        job.due = due
        self._cancel_timer(job.id)
        await self._async_announce(job, "updated")
        return job

    async def async_run_now(self, job_id: str) -> Job:
        """Run a pending job immediately instead of at its due time."""
        self._require_pending(job_id)
        self._launch(job_id)
        return self._jobs[job_id]

    async def async_reschedule(self, job_id: str, due: datetime) -> Job:
        """Queue a copy of any job with a new id and due time."""
        source = self.get(job_id)
        clone = Job(
            id=new_job_id(),
            kind=source.kind,
            status=JobStatus.PENDING,
            due=due,
            created_at=dt_util.utcnow(),
            finished_at=None,
            summary=source.summary,
            original_text=source.original_text,
            intent=copy.deepcopy(source.intent),
            action=copy.deepcopy(source.action),
            raw_action=source.raw_action,
            targets=copy.deepcopy(source.targets),
            source=copy.deepcopy(source.source),
            result=Result(),
        )
        return await self.async_add(clone)

    async def async_delete_history(self, job_ids: list[str]) -> int:
        """Delete finished jobs by id; return how many were removed."""
        removed = [
            self._jobs.pop(job_id)
            for job_id in dict.fromkeys(job_ids)
            if job_id in self._jobs and self._jobs[job_id].status in HISTORY_STATUSES
        ]
        if removed:
            await self._async_save()
            for job in removed:
                self._notify("removed", job)
        return len(removed)

    async def async_clear_history(self) -> int:
        """Delete every finished job; return how many were removed."""
        return await self.async_delete_history([j.id for j in self.history()])

    def update_options(self, options: ManagerOptions) -> None:
        """Use new options from the next schedule, run or prune on."""
        self._options = options

    def subscribe(self, cb: Callable[[JobChange], None]) -> Callable[[], None]:
        """Call ``cb`` synchronously on every change; return an unsubscribe function."""
        self._subscribers.append(cb)

        def _unsubscribe() -> None:
            if cb in self._subscribers:
                self._subscribers.remove(cb)

        return _unsubscribe

    # Internals

    async def _async_announce(self, job: Job, kind: Literal["added", "updated"]) -> None:
        """Save, fire the scheduled event and notify, and only then arm the timer."""
        self._settling.add(job.id)
        try:
            await self._async_save()
        finally:
            self._settling.discard(job.id)
        fire_job_event(self._hass, EVENT_JOB_SCHEDULED, job)
        self._notify(kind, job)
        self._schedule(job)

    def _require_pending(self, job_id: str) -> Job:
        job = self.get(job_id)
        if job.status is not JobStatus.PENDING or job_id in self._in_flight:
            raise JobStateError(f"Job {job_id} is {job.status}, not pending")
        return job

    def _cancel(self, job: Job, by: str) -> None:
        self._cancel_timer(job.id)
        job.status = JobStatus.CANCELLED
        job.result.cancelled_by = by
        job.finished_at = dt_util.utcnow()

    def _schedule(self, job: Job) -> None:
        self._cancel_timer(job.id)
        job_id = job.id

        @callback
        def _due(_now: datetime) -> None:
            self._timers.pop(job_id, None)
            self._launch(job_id)

        self._timers[job_id] = async_track_point_in_utc_time(self._hass, _due, job.due)

    def _cancel_timer(self, job_id: str) -> None:
        if (unsub := self._timers.pop(job_id, None)) is not None:
            unsub()

    @callback
    def _sweep(self, _now: datetime) -> None:
        now = dt_util.utcnow()
        for job in list(self._jobs.values()):
            if job.status is JobStatus.PENDING and job.due <= now:
                self._launch(job.id)

    @callback
    def _launch(self, job_id: str) -> None:
        """Start a pending job in the background, at most once."""
        job = self._jobs.get(job_id)
        if job is None or job.status is not JobStatus.PENDING or job_id in self._in_flight or job_id in self._settling:
            return
        self._in_flight.add(job_id)
        self._cancel_timer(job_id)
        job.status = JobStatus.RUNNING
        self._notify("updated", job)
        task = self._hass.async_create_background_task(self._async_run(job), name=f"at job {job_id}")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _async_run(self, job: Job) -> None:
        try:
            try:
                await self._async_save()
                await self._executor.async_execute(job)
            except JobExecutionError as err:
                job.status = JobStatus.FAILED
                job.result.error = str(err)
            except Exception as err:  # noqa: BLE001 - A save or executor bug must still finish the job.
                LOGGER.exception("Job %s raised an unexpected error", job.id)
                job.status = JobStatus.FAILED
                job.result.error = str(err) or type(err).__name__
            else:
                job.status = JobStatus.DONE
            job.finished_at = dt_util.utcnow()
        finally:
            self._in_flight.discard(job.id)
        await self._async_after_finish([job])

    async def _async_after_finish(self, jobs: list[Job]) -> None:
        self._prune()
        await self._async_save()
        for job in jobs:
            fire_job_event(self._hass, _FINISH_EVENTS[job.status], job)
            if job.id in self._jobs:
                self._notify("updated", job)

    def _prune(self) -> None:
        kept = prune_history(
            list(self._jobs.values()),
            dt_util.utcnow(),
            self._options.history_days,
            self._options.history_max,
        )
        kept_ids = {job.id for job in kept}
        removed = [job for job in self._jobs.values() if job.id not in kept_ids]
        self._jobs = {job.id: job for job in kept}
        for job in removed:
            self._notify("removed", job)

    async def _async_save(self) -> None:
        await self._store.async_save(list(self._jobs.values()))

    def _notify(self, kind: Literal["added", "updated", "removed"], job: Job) -> None:
        change = JobChange(kind, job)
        for cb in list(self._subscribers):
            cb(change)
