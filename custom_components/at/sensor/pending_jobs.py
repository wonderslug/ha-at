"""Sensor counting the pending jobs."""

from typing import TYPE_CHECKING, Any

from custom_components.at.entity.base import AtEntity
from homeassistant.components.sensor import SensorEntity, SensorStateClass

if TYPE_CHECKING:
    from custom_components.at.core.manager import JobChange
    from custom_components.at.data import AtConfigEntry


class AtPendingJobsSensor(AtEntity, SensorEntity):
    """The number of pending jobs."""

    _attr_should_poll = False
    _attr_translation_key = "pending_jobs"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: AtConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(entry)
        self._manager = entry.runtime_data.manager
        self._attr_unique_id = f"{entry.entry_id}_pending_jobs"
        # Pin the id: the device name would otherwise yield sensor.scheduled_jobs_pending_jobs.
        self.entity_id = "sensor.at_pending_jobs"

    async def async_added_to_hass(self) -> None:
        """Follow the job queue."""
        self.async_on_remove(self._manager.subscribe(self._on_change))

    def _on_change(self, _change: JobChange) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> int:
        """Return the number of pending jobs."""
        return len(self._manager.pending())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the pending jobs in due order."""
        return {
            "jobs": [
                {"id": job.id, "due": job.due.isoformat(), "summary": job.summary} for job in self._manager.pending()
            ]
        }
