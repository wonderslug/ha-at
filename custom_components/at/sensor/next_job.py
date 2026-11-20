"""Sensor for the next pending job."""

from typing import TYPE_CHECKING, Any

from custom_components.at.entity.base import AtEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription

if TYPE_CHECKING:
    from datetime import datetime

    from custom_components.at.data import AtConfigEntry

ENTITY_DESCRIPTION = SensorEntityDescription(
    key="next_job",
    translation_key="next_job",
    device_class=SensorDeviceClass.TIMESTAMP,
)


class AtNextJobSensor(AtEntity, SensorEntity):
    """The due time of the earliest pending job."""

    _unrecorded_attributes = frozenset({"job_id", "summary"})

    def __init__(self, entry: AtConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(entry, ENTITY_DESCRIPTION)
        # Pin the id: the device name would otherwise yield sensor.scheduled_jobs_next_job.
        self.entity_id = "sensor.at_next_job"

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
