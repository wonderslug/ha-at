"""Sensor entity for at."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from custom_components.at.entity import AtEntity
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.helpers.typing import StateType


@dataclass(frozen=True, kw_only=True)
class AtSensorEntityDescription(SensorEntityDescription):
    """Describes a sensor and how to read it from coordinator data."""

    value_fn: Callable[[dict[str, Any]], StateType]


class AtSensor(SensorEntity, AtEntity):
    """Sensor backed by one value in the coordinator payload."""

    entity_description: AtSensorEntityDescription

    @property
    def native_value(self) -> StateType:
        """Return the value read from coordinator data."""
        return self.entity_description.value_fn(self.coordinator.data)
