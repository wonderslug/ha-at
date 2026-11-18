"""Sensor for the next pending job."""

from typing import TYPE_CHECKING, Any

from custom_components.at.entity.base import AtEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

if TYPE_CHECKING:
    from datetime import datetime

    from custom_components.at.core.manager import JobChange
    from custom_components.at.data import AtConfigEntry


class AtNextJobSensor(AtEntity, SensorEntity):
    """The due time of the earliest pending job."""

    _attr_should_poll = False
    _attr_translation_key = "next_job"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, entry: AtConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(entry)
        self._manager = entry.runtime_data.manager
        self._attr_unique_id = f"{entry.entry_id}_next_job"
        # Pin the id: the device name would otherwise yield sensor.at_placeholder_next_job.
        self.entity_id = "sensor.at_next_job"

    async def async_added_to_hass(self) -> None:
        """Follow the job queue."""
        self.async_on_remove(self._manager.subscribe(self._on_change))

    def _on_change(self, _change: JobChange) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> datetime | None:
        """Return the earliest due time, or None when nothing is pending."""
        pending = self._manager.pending()
        return pending[0].due if pending else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the id and summary of the next job."""
        pending = self._manager.pending()
        if not pending:
            return {"job_id": None, "summary": None}
        return {"job_id": pending[0].id, "summary": pending[0].summary}
