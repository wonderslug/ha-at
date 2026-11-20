"""Versioned persistence for jobs."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from custom_components.at.const import LOGGER, STORAGE_KEY, STORAGE_MINOR_VERSION, STORAGE_VERSION
from homeassistant.helpers.storage import Store

from .models import Job, JobStatus

if TYPE_CHECKING:
    from collections.abc import Iterable

    from homeassistant.core import HomeAssistant

HISTORY_STATUSES = frozenset({JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.MISSED})


async def _async_migrate_func(
    old_major_version: int,
    old_minor_version: int,
    old_data: dict[str, Any],
) -> dict[str, Any]:
    """Migrate stored data; only the current major version is known."""
    if old_major_version == STORAGE_VERSION:
        return old_data
    msg = f"Unknown storage version {old_major_version}"
    raise NotImplementedError(msg)


class _JobStorage(Store[dict[str, Any]]):
    """Store with migration support."""

    async def _async_migrate_func(
        self,
        old_major_version: int,
        old_minor_version: int,
        old_data: dict[str, Any],
    ) -> dict[str, Any]:
        return await _async_migrate_func(old_major_version, old_minor_version, old_data)


class JobStore:
    """
    Load and save jobs.

    A stored record that cannot be read is set aside under ``unreadable`` and written back unchanged on every
    save, so one bad record neither stops the integration loading nor is lost.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialise the store."""
        self._store = _JobStorage(hass, STORAGE_VERSION, STORAGE_KEY, minor_version=STORAGE_MINOR_VERSION)
        self._unreadable: list[Any] = []

    async def async_load(self) -> list[Job]:
        """Return every stored job that can be read."""
        data = await self._store.async_load()
        if not data:
            return []
        self._unreadable = list(data.get("unreadable", []))
        jobs: list[Job] = []
        for item in data.get("jobs", []):
            try:
                job = Job.from_dict(item)
            except (AttributeError, KeyError, TypeError, ValueError) as err:
                record_id = item.get("id") if isinstance(item, dict) else None
                LOGGER.warning("Stored job %s cannot be read and was set aside: %r", record_id, err)
                self._unreadable.append(item)
            else:
                jobs.append(job)
        return jobs

    async def async_remove(self) -> None:
        """Delete the stored jobs."""
        await self._store.async_remove()

    async def async_save(self, jobs: Iterable[Job]) -> None:
        """Persist the jobs."""
        data: dict[str, Any] = {"jobs": [job.to_dict() for job in jobs]}
        if self._unreadable:
            data["unreadable"] = self._unreadable
        await self._store.async_save(data)


def prune_history(jobs: list[Job], now: datetime, days: int, max_count: int) -> list[Job]:
    """
    Keep non-history jobs plus the newest ``max_count`` history jobs finished within ``days``.

    A history job without ``finished_at`` cannot be aged, so it is dropped.
    """
    cutoff = now - timedelta(days=days)
    history = [j for j in jobs if j.status in HISTORY_STATUSES]
    keep = sorted(
        (j for j in history if j.finished_at is not None and j.finished_at >= cutoff),
        key=lambda j: j.finished_at or cutoff,
        reverse=True,
    )[:max_count]
    keep_ids = {id(j) for j in keep}
    return [j for j in jobs if j.status not in HISTORY_STATUSES or id(j) in keep_ids]
