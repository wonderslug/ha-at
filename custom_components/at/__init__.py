"""
Custom integration to integrate at with Home Assistant.

For more details about this integration, please refer to:
https://github.com/PLACEHOLDER_OWNER/ha-at
"""

from typing import TYPE_CHECKING

import homeassistant.helpers.config_validation as cv

from .const import DOMAIN
from .data import AtRuntimeData
from .service_actions import async_setup_services

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import AtConfigEntry

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """
    Register the service actions.

    Returns:
        True once the actions are registered.

    """
    async_setup_services(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AtConfigEntry,
) -> bool:
    """
    Set up a config entry.

    Returns:
        True once the runtime data is in place.

    """
    entry.runtime_data = AtRuntimeData()
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AtConfigEntry,
) -> bool:
    """
    Unload a config entry.

    Returns:
        True, since no platforms are forwarded yet.

    """
    return True
