"""Sensor counting the pending jobs."""

from typing import TYPE_CHECKING, Any

from custom_components.at.entity.base import AtEntity
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass

if TYPE_CHECKING:
    from custom_components.at.data import AtConfigEntry

ENTITY_DESCRIPTION = SensorEntityDescription(
    key="pending_jobs",
    translation_key="pending_jobs",
    state_class=SensorStateClass.MEASUREMENT,
)


class AtPendingJobsSensor(AtEntity, SensorEntity):
    """The number of pending jobs."""

    _unrecorded_attributes = frozenset({"jobs"})

    def __init__(self, entry: AtConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(entry, ENTITY_DESCRIPTION)
        # Pin the id: the device name would otherwise yield sensor.scheduled_jobs_pending_jobs.
        self.entity_id = "sensor.at_pending_jobs"

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
