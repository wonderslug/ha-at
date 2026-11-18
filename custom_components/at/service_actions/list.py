"""The at.list action."""

from typing import TYPE_CHECKING

from custom_components.at.core.models import Job, JobStatus
from homeassistant.util import dt as dt_util

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
    # The datetime selector sends naive values; as_utc reads those as Home Assistant local time.
    start = dt_util.as_utc(call.data["start"]) if "start" in call.data else None
    end = dt_util.as_utc(call.data["end"]) if "end" in call.data else None

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
