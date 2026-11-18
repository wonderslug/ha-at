"""Persisted job records (pure Python, no Home Assistant imports)."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
import secrets
from typing import Any


class JobStatus(StrEnum):
    """Lifecycle state of a job."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"
    MISSED = "missed"


class JobKind(StrEnum):
    """What a job runs."""

    INTENT = "intent"
    ACTION = "action"


class Via(StrEnum):
    """How a job was created."""

    VOICE = "voice"
    LLM = "llm"
    PANEL = "panel"
    TODO = "todo"
    SERVICE = "service"


@dataclass
class IntentSpec:
    """A Home Assistant intent to replay when the job is due."""

    type: str
    slots: dict[str, Any]
    language: str
    device_id: str | None = None
    satellite_id: str | None = None


@dataclass
class Targets:
    """What the job acts on, used for listing and cancel by name."""

    entity_ids: list[str] = field(default_factory=list)
    area_ids: list[str] = field(default_factory=list)
    floor_ids: list[str] = field(default_factory=list)
    names: list[str] = field(default_factory=list)


@dataclass
class Source:
    """Where the job came from."""

    via: Via
    user_id: str | None = None
    device_id: str | None = None
    agent_id: str | None = None


@dataclass
class Result:
    """Outcome details of a finished job."""

    error: str | None = None
    cancelled_by: str | None = None


def _dt(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(UTC).isoformat()


def _parse(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


@dataclass
class Job:
    """A scheduled one-shot job."""

    id: str
    kind: JobKind
    status: JobStatus
    due: datetime
    created_at: datetime
    finished_at: datetime | None
    summary: str
    original_text: str | None
    intent: IntentSpec | None
    action: list[dict[str, Any]] | None
    raw_action: bool
    targets: Targets
    source: Source
    result: Result

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict."""
        return {
            "id": self.id,
            "kind": str(self.kind),
            "status": str(self.status),
            "due": _dt(self.due),
            "created_at": _dt(self.created_at),
            "finished_at": _dt(self.finished_at),
            "summary": self.summary,
            "original_text": self.original_text,
            "intent": None
            if self.intent is None
            else {
                "type": self.intent.type,
                "slots": self.intent.slots,
                "language": self.intent.language,
                "device_id": self.intent.device_id,
                "satellite_id": self.intent.satellite_id,
            },
            "action": self.action,
            "raw_action": self.raw_action,
            "targets": {
                "entity_ids": list(self.targets.entity_ids),
                "area_ids": list(self.targets.area_ids),
                "floor_ids": list(self.targets.floor_ids),
                "names": list(self.targets.names),
            },
            "source": {
                "via": str(self.source.via),
                "user_id": self.source.user_id,
                "device_id": self.source.device_id,
                "agent_id": self.source.agent_id,
            },
            "result": {
                "error": self.result.error,
                "cancelled_by": self.result.cancelled_by,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Job:
        """Build a job from ``to_dict`` output."""
        intent = data.get("intent")
        targets = data.get("targets") or {}
        source = data["source"]
        result = data.get("result") or {}
        due = _parse(data["due"])
        created_at = _parse(data["created_at"])
        if due is None or created_at is None:
            msg = "job is missing due or created_at"
            raise ValueError(msg)
        return cls(
            id=data["id"],
            kind=JobKind(data["kind"]),
            status=JobStatus(data["status"]),
            due=due,
            created_at=created_at,
            finished_at=_parse(data.get("finished_at")),
            summary=data["summary"],
            original_text=data.get("original_text"),
            intent=None
            if intent is None
            else IntentSpec(
                type=intent["type"],
                slots=intent.get("slots") or {},
                language=intent["language"],
                device_id=intent.get("device_id"),
                satellite_id=intent.get("satellite_id"),
            ),
            action=data.get("action"),
            raw_action=bool(data.get("raw_action", False)),
            targets=Targets(
                entity_ids=list(targets.get("entity_ids", [])),
                area_ids=list(targets.get("area_ids", [])),
                floor_ids=list(targets.get("floor_ids", [])),
                names=list(targets.get("names", [])),
            ),
            source=Source(
                via=Via(source["via"]),
                user_id=source.get("user_id"),
                device_id=source.get("device_id"),
                agent_id=source.get("agent_id"),
            ),
            result=Result(error=result.get("error"), cancelled_by=result.get("cancelled_by")),
        )


def new_job_id() -> str:
    """Return a new 8 character lowercase hex id."""
    return secrets.token_hex(4)
