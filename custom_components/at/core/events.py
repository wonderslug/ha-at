"""Bus events fired on job lifecycle changes."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .models import Job


def fire_job_event(hass: HomeAssistant, event_type: str, job: Job) -> None:
    """Fire ``event_type`` with the job's public payload."""
    hass.bus.async_fire(
        event_type,
        {
            "job_id": job.id,
            "summary": job.summary,
            "due": job.due.isoformat(),
            "status": str(job.status),
            "via": str(job.source.via),
        },
    )
