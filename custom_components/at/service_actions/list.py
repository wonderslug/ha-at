"""The at.list action."""

from typing import TYPE_CHECKING

from custom_components.at.core.models import Job, JobStatus

from .common import async_get_manager

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse

_QUEUED = (JobStatus.PENDING, JobStatus.RUNNING)


async def async_handle_list(hass: HomeAssistant, call: ServiceCall) -> ServiceResponse:
    """
    List the queued and finished jobs.

    Returns:
        The queued jobs as ``pending`` and the finished ones as ``history``.

    """
    manager = async_get_manager(hass)
    statuses = {JobStatus(s) for s in call.data.get("status", [])}
    start = call.data.get("start")
    end = call.data.get("end")

    def keep(job: Job) -> bool:
        return (
            (not statuses or job.status in statuses)
            and (start is None or job.due >= start)
            and (end is None or job.due <= end)
        )

    queued = [*manager.pending(), *manager.running()]
    queued.sort(key=lambda j: j.due)
    return {
        "pending": [j.to_dict() for j in queued if keep(j)],
        "history": [j.to_dict() for j in manager.history() if keep(j)],
    }
