"""The at.cancel action."""

from typing import TYPE_CHECKING

from custom_components.at.core.errors import JobStateError
from custom_components.at.core.models import Via
from homeassistant.helpers import config_validation as cv

from .common import async_get_job, async_get_manager, job_not_pending

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse


async def async_handle_cancel(hass: HomeAssistant, call: ServiceCall) -> ServiceResponse:
    """
    Cancel pending jobs by id, or every pending job.

    Returns:
        The ids that were cancelled.

    """
    manager = async_get_manager(hass)
    if call.data.get("all"):
        ids = [job.id for job in manager.pending()]
    else:
        ids = cv.ensure_list(call.data["job_id"])
    for job_id in ids:
        async_get_job(manager, job_id, pending=True)
    try:
        cancelled = await manager.async_cancel_many(ids, str(Via.SERVICE), call.context)
    except JobStateError as err:
        raise job_not_pending(", ".join(ids)) from err
    return {"cancelled": [job.id for job in cancelled]}
