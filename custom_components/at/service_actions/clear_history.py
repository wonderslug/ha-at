"""The at.clear_history action."""

from typing import TYPE_CHECKING

from .common import async_get_manager

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse


async def async_handle_clear_history(hass: HomeAssistant, call: ServiceCall) -> ServiceResponse:
    """
    Delete every finished job.

    Returns:
        How many jobs were removed.

    """
    return {"removed": await async_get_manager(hass).async_clear_history()}
