"""Base entity class for at."""

from typing import TYPE_CHECKING

from custom_components.at.const import DISPLAY_NAME, DOMAIN
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity

if TYPE_CHECKING:
    from custom_components.at.data import AtConfigEntry


class AtEntity(Entity):
    """Base entity attaching to the single service-type device of the entry."""

    _attr_has_entity_name = True

    def __init__(self, entry: AtConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=DISPLAY_NAME,
            entry_type=DeviceEntryType.SERVICE,
        )
