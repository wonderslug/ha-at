"""
Custom integration to integrate at with Home Assistant.

For more details about this integration, please refer to:
https://github.com/PLACEHOLDER_OWNER/ha-at
"""

from datetime import timedelta
from typing import TYPE_CHECKING

import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_GRACE_MINUTES,
    CONF_HISTORY_DAYS,
    CONF_HISTORY_MAX,
    DEFAULT_GRACE_MINUTES,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_HISTORY_MAX,
    DOMAIN,
)
from .core.errors import JobExecutionError
from .core.manager import JobManager, ManagerOptions
from .core.store import JobStore
from .data import AtRuntimeData
from .service_actions import async_setup_services

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .core.models import Job
    from .data import AtConfigEntry

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


class _UnconfiguredExecutor:
    """Placeholder until the real executor lands; every job fails."""

    async def async_execute(self, job: Job) -> None:
        raise JobExecutionError("executor not configured")


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
    manager = JobManager(hass, JobStore(hass), _UnconfiguredExecutor(), manager_options(entry))
    await manager.async_start()
    entry.runtime_data = AtRuntimeData(manager=manager)
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
    await entry.runtime_data.manager.async_stop()
    return True
