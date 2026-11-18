"""Bus events fired on job lifecycle changes."""

from typing import TYPE_CHECKING

from custom_components.at.const import EVENT_JOB_FAILED

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .models import Job


def fire_job_event(hass: HomeAssistant, event_type: str, job: Job) -> None:
    """Fire ``event_type`` with the job's public payload."""
    data: dict[str, str | None] = {
        "job_id": job.id,
        "summary": job.summary,
        "due": job.due.isoformat(),
        "status": str(job.status),
        "via": str(job.source.via),
    }
    if event_type == EVENT_JOB_FAILED:
        data["error"] = job.result.error
    hass.bus.async_fire(event_type, data)
