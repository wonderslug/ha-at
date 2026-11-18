"""Helpers shared by the service action handlers."""

from typing import TYPE_CHECKING

from custom_components.at.const import DOMAIN
from homeassistant.exceptions import ServiceValidationError, Unauthorized

if TYPE_CHECKING:
    from custom_components.at.core.manager import JobManager
    from homeassistant.core import HomeAssistant, ServiceCall


def async_get_manager(hass: HomeAssistant) -> JobManager:
    """
    Return the job manager of the loaded config entry.

    Raises:
        ServiceValidationError: no entry is loaded.

    """
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        return entry.runtime_data.manager
    raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_loaded")


async def async_require_admin(hass: HomeAssistant, call: ServiceCall) -> None:
    """
    Reject a call made by a user who is not an administrator.

    A call with no user (an automation or script) is allowed.

    Raises:
        Unauthorized: the calling user is not an administrator.

    """
    if call.context.user_id is None:
        return
    user = await hass.auth.async_get_user(call.context.user_id)
    if user is None or not user.is_admin:
        raise Unauthorized(context=call.context)
