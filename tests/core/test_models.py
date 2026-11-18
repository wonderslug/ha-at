"""Tests for the job model."""

from datetime import UTC, datetime, timedelta
import json
import re

from custom_components.at.core.models import (
    IntentSpec,
    Job,
    JobKind,
    JobStatus,
    Result,
    Source,
    Targets,
    Via,
    new_job_id,
)

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)


def _intent_job() -> Job:
    return Job(
        id="abcd1234",
        kind=JobKind.INTENT,
        status=JobStatus.PENDING,
        due=NOW + timedelta(minutes=10),
        created_at=NOW,
        finished_at=None,
        summary="turn off the lights",
        original_text="turn off the lights in 10 minutes",
        intent=IntentSpec(
            type="HassTurnOff",
            slots={"name": {"value": "lights"}},
            language="en",
            device_id="dev1",
            satellite_id=None,
        ),
        action=None,
        raw_action=False,
        targets=Targets(entity_ids=["light.a"], area_ids=[], floor_ids=[], names=["lights"]),
        source=Source(via=Via.VOICE, user_id="u1", device_id="dev1", agent_id=None),
        result=Result(),
    )


def _action_job() -> Job:
    return Job(
        id="deadbeef",
        kind=JobKind.ACTION,
        status=JobStatus.FAILED,
        due=NOW,
        created_at=NOW - timedelta(hours=1),
        finished_at=NOW,
        summary="do a thing",
        original_text=None,
        intent=None,
        action=[{"action": "light.turn_on", "target": {"entity_id": "light.a"}}],
        raw_action=True,
        targets=Targets(entity_ids=[], area_ids=["kitchen"], floor_ids=["f1"], names=[]),
        source=Source(via=Via.SERVICE, user_id=None, device_id=None, agent_id="agent"),
        result=Result(error="boom", cancelled_by="u2"),
    )


def test_job_roundtrip() -> None:
    for job in (_intent_job(), _action_job()):
        data = json.loads(json.dumps(job.to_dict()))
        assert Job.from_dict(data) == job


def test_to_dict_is_plain_json() -> None:
    data = _intent_job().to_dict()
    assert data["status"] == "pending"
    assert data["due"] == "2026-11-17T12:10:00+00:00"
    assert data["source"]["via"] == "voice"


def test_new_job_id_format() -> None:
    assert re.fullmatch(r"[0-9a-f]{8}", new_job_id())
