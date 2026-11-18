"""
Custom integration to integrate at with Home Assistant.

For more details about this integration, please refer to:
https://github.com/wonderslug/ha-at
"""

from collections.abc import Callable
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
from .panel import async_register_panel, async_remove_panel
from .service_actions import async_setup_services
from .voice.intents import async_register_intents, async_remove_intents
from .voice.triggers import async_setup_triggers
from .websocket_api import async_register_commands

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import AtConfigEntry

PLATFORMS = [Platform.SENSOR, Platform.TODO]
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
    Register the service actions and websocket commands.

    Returns:
        True once they are registered.

    """
    async_setup_services(hass)
    async_register_commands(hass)
    return True


def _register_voice(hass: HomeAssistant, entry: AtConfigEntry) -> Callable[[], None]:
    """
    Register the voice sentences the options ask for.

    Returns:
        The callback that unregisters them; a no-op when none could be registered.

    """
    if (pack := get_language_pack(hass.config.language)) is None:
        LOGGER.info("at has no voice sentences for language %s; use the intents or an LLM agent", hass.config.language)
        return _noop
    defer_relative = entry.options.get(CONF_DEFER_RELATIVE, DEFAULT_DEFER_RELATIVE)
    try:
        return async_setup_triggers(hass, pack, defer_relative=defer_relative)
    except Exception as err:  # noqa: BLE001 - Home Assistant internals; without sentences, at still works
        LOGGER.warning(
            "Could not register the at voice sentences, so only the actions, panel and LLM tools work: %s", err
        )
        return _noop


def _noop() -> None:
    """Stand in for an unregister callback when nothing was registered."""


async def _async_options_updated(hass: HomeAssistant, entry: AtConfigEntry) -> None:
    """Apply saved options in place, so a running job is never interrupted by a reload."""
    runtime = entry.runtime_data
    runtime.manager.update_options(manager_options(entry))
    runtime.unregister_voice()
    runtime.unregister_voice = _register_voice(hass, entry)
    async_remove_panel(hass)
    await async_register_panel(hass, entry)


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
    # Each step registers its own teardown as soon as it succeeds, so a step that raises later
    # leaves nothing running: Home Assistant runs these callbacks when setup fails, too.
    entry.async_on_unload(manager.async_stop)
    entry.runtime_data = AtRuntimeData(manager=manager)
    async_register_intents(hass)
    entry.async_on_unload(lambda: async_remove_intents(hass))
    await async_register_panel(hass, entry)
    entry.async_on_unload(lambda: async_remove_panel(hass))
    entry.runtime_data.unregister_voice = _register_voice(hass, entry)
    entry.async_on_unload(lambda: entry.runtime_data.unregister_voice())
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AtConfigEntry,
) -> bool:
    """
    Unload a config entry.

    Returns:
        True once the platforms are unloaded; False if a platform fails to unload.

    """
    # The intents, the panel and the manager are torn down by the entry's on-unload callbacks.
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(
    hass: HomeAssistant,
    entry: AtConfigEntry,
) -> None:
    """Delete the stored jobs when the integration is removed."""
    await JobStore(hass).async_remove()
