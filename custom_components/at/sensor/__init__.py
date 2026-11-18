"""Sensor platform for at."""

from typing import TYPE_CHECKING

from .next_job import AtNextJobSensor
from .pending_jobs import AtPendingJobsSensor

if TYPE_CHECKING:
    from custom_components.at.data import AtConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AtConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities([AtNextJobSensor(entry), AtPendingJobsSensor(entry)])
