"""The at.run_now action."""

from typing import TYPE_CHECKING

from .common import async_get_manager, async_require_admin

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall


async def async_handle_run_now(hass: HomeAssistant, call: ServiceCall) -> None:
    """Run a pending job now; a raw action needs an administrator."""
    manager = async_get_manager(hass)
    job = manager.get(call.data["job_id"])
    if job.raw_action:
        await async_require_admin(hass, call)
    await manager.async_run_now(job.id)
