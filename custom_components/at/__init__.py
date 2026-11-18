"""
Custom integration to integrate at with Home Assistant.

For more details about this integration, please refer to:
https://github.com/PLACEHOLDER_OWNER/ha-at
"""

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import Platform
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_DEFER_RELATIVE,
    CONF_GRACE_MINUTES,
    CONF_HISTORY_DAYS,
    CONF_HISTORY_MAX,
    DEFAULT_DEFER_RELATIVE,
    DEFAULT_GRACE_MINUTES,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_HISTORY_MAX,
    DOMAIN,
    LOGGER,
)
from .core.executor import JobExecutor
from .core.manager import JobManager, ManagerOptions
from .core.store import JobStore
from .data import AtRuntimeData
from .lang import get_language_pack
from .service_actions import async_setup_services
from .voice.intents import async_register_intents, async_remove_intents
from .voice.triggers import async_setup_triggers

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import AtConfigEntry

PLATFORMS = [Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def manager_options(entry: AtConfigEntry) -> ManagerOptions:
    """
    Build manager options from the entry options.

    Returns:
        The options, with defaults for anything unset.

    """
    options = entry.options
    return ManagerOptions(
        grace=timedelta(minutes=options.get(CONF_GRACE_MINUTES, DEFAULT_GRACE_MINUTES)),
        history_days=options.get(CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS),
        history_max=options.get(CONF_HISTORY_MAX, DEFAULT_HISTORY_MAX),
    )


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
        True once the job manager is running.

    """
    manager = JobManager(hass, JobStore(hass), JobExecutor(hass), manager_options(entry))
    await manager.async_start()
    entry.runtime_data = AtRuntimeData(manager=manager)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_register_intents(hass)
    if (pack := get_language_pack(hass.config.language)) is None:
        LOGGER.info("at has no voice sentences for language %s; use the intents or an LLM agent", hass.config.language)
    else:
        defer_relative = entry.options.get(CONF_DEFER_RELATIVE, DEFAULT_DEFER_RELATIVE)
        entry.async_on_unload(async_setup_triggers(hass, pack, defer_relative=defer_relative))
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AtConfigEntry,
) -> bool:
    """
    Unload a config entry.

    Returns:
        True once the platforms and the manager are stopped; False if a platform fails to unload.

    """
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    async_remove_intents(hass)
    await entry.runtime_data.manager.async_stop()
    return True
