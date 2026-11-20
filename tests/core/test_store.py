"""Tests for the job store."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from custom_components.at.const import STORAGE_KEY, STORAGE_MINOR_VERSION, STORAGE_VERSION
from custom_components.at.core.models import Job, JobKind, JobStatus, Result, Source, Targets, Via
from custom_components.at.core.store import JobStore, _async_migrate_func, prune_history
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


def _stored(records: list[Any]) -> dict[str, Any]:
    return {
        "version": STORAGE_VERSION,
        "minor_version": STORAGE_MINOR_VERSION,
        "key": STORAGE_KEY,
        "data": {"jobs": records},
    }


async def test_store_sets_aside_unreadable_records(
    hass: HomeAssistant, hass_storage: dict[str, Any], caplog: pytest.LogCaptureFixture
) -> None:
    good = _job("00000001")
    missing_source = {k: v for k, v in _job("00000002").to_dict().items() if k != "source"}
    bad_status = {**_job("00000003").to_dict(), "status": "exploded"}
    hass_storage[STORAGE_KEY] = _stored([good.to_dict(), missing_source, bad_status, "not a record"])

    store = JobStore(hass)
    assert await store.async_load() == [good]
    assert "00000002" in caplog.text
    assert "00000003" in caplog.text

    await store.async_save([good])
    saved = hass_storage[STORAGE_KEY]["data"]
    assert saved["jobs"] == [good.to_dict()]
    assert saved["unreadable"] == [missing_source, bad_status, "not a record"]

    reloaded = JobStore(hass)
    assert await reloaded.async_load() == [good]
    await reloaded.async_save([good])
    assert hass_storage[STORAGE_KEY]["data"]["unreadable"] == [missing_source, bad_status, "not a record"]


async def test_store_without_unreadable_records_writes_no_unreadable_key(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    await JobStore(hass).async_save([_job("00000001")])
    assert "unreadable" not in hass_storage[STORAGE_KEY]["data"]


async def test_migrate_keeps_current_major_version() -> None:
    data = {"jobs": [_job("00000001").to_dict()]}
    assert await _async_migrate_func(STORAGE_VERSION, STORAGE_MINOR_VERSION + 1, data) is data


async def test_migrate_rejects_unknown_major_version() -> None:
    with pytest.raises(NotImplementedError):
        await _async_migrate_func(STORAGE_VERSION + 1, 1, {"jobs": []})


async def test_store_loads_data_written_with_a_newer_minor_version(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    job = _job("00000001")
    hass_storage[STORAGE_KEY] = {**_stored([job.to_dict()]), "minor_version": STORAGE_MINOR_VERSION + 1}
    assert await JobStore(hass).async_load() == [job]


def test_prune_history_by_age_and_count() -> None:
    pending = [_job(f"p{i}") for i in range(3)]
    recent = [_job(f"r{i:03d}", JobStatus.DONE, NOW - timedelta(hours=i + 1)) for i in range(90)]
    old = [_job(f"o{i:03d}", JobStatus.DONE, NOW - timedelta(days=8, hours=i)) for i in range(30)]
    jobs = pending + recent + old

    kept = prune_history(jobs, NOW, days=7, max_count=100)
    assert {j.id for j in kept} == {j.id for j in pending + recent}

    kept = prune_history(jobs, NOW, days=7, max_count=50)
    assert {j.id for j in kept} == {j.id for j in pending + recent[:50]}
