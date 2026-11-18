"""Tests for the job store."""

from datetime import UTC, datetime, timedelta
from typing import Any

from custom_components.at.core.models import Job, JobKind, JobStatus, Result, Source, Targets, Via
from custom_components.at.core.store import JobStore, prune_history
from homeassistant.core import HomeAssistant

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)


def _job(
    job_id: str,
    status: JobStatus = JobStatus.PENDING,
    finished_at: datetime | None = None,
) -> Job:
    return Job(
        id=job_id,
        kind=JobKind.ACTION,
        status=status,
        due=NOW,
        created_at=NOW,
        finished_at=finished_at,
        summary="s",
        original_text=None,
        intent=None,
        action=[{"action": "x.y"}],
        raw_action=True,
        targets=Targets(entity_ids=[], area_ids=[], floor_ids=[], names=[]),
        source=Source(via=Via.SERVICE, user_id=None, device_id=None, agent_id=None),
        result=Result(),
    )


async def test_store_persists_across_instances(hass: HomeAssistant, hass_storage: dict[str, Any]) -> None:
    jobs = [_job("00000001"), _job("00000002", JobStatus.DONE, NOW)]
    await JobStore(hass).async_save(jobs)
    assert await JobStore(hass).async_load() == jobs


async def test_store_empty_returns_empty_list(hass: HomeAssistant, hass_storage: dict[str, Any]) -> None:
    assert await JobStore(hass).async_load() == []


def test_prune_history_by_age_and_count() -> None:
    pending = [_job(f"p{i}") for i in range(3)]
    recent = [_job(f"r{i:03d}", JobStatus.DONE, NOW - timedelta(hours=i + 1)) for i in range(90)]
    old = [_job(f"o{i:03d}", JobStatus.DONE, NOW - timedelta(days=8, hours=i)) for i in range(30)]
    jobs = pending + recent + old

    kept = prune_history(jobs, NOW, days=7, max_count=100)
    assert {j.id for j in kept} == {j.id for j in pending + recent}

    kept = prune_history(jobs, NOW, days=7, max_count=50)
    assert {j.id for j in kept} == {j.id for j in pending + recent[:50]}
