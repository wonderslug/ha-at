"""The at.run_now action."""

from typing import TYPE_CHECKING

from custom_components.at.core.errors import JobStateError
from custom_components.at.core.models import JobStatus

from .common import async_get_job, async_get_manager, async_require_admin, job_not_pending

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall


async def async_handle_run_now(hass: HomeAssistant, call: ServiceCall) -> None:
    """Run a pending job now; a raw action needs an administrator, checked before anything else about the job."""
    manager = async_get_manager(hass)
    job = async_get_job(manager, call.data["job_id"])
    if job.raw_action:
        await async_require_admin(hass, call.context)
    if job.status is not JobStatus.PENDING:
        raise job_not_pending(job.id)
    try:
        await manager.async_run_now(job.id)
    except JobStateError as err:
        raise job_not_pending(job.id) from err
