"""Base entity class for at."""

from typing import TYPE_CHECKING

from custom_components.at.const import DISPLAY_NAME, DOMAIN
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription

if TYPE_CHECKING:
    from custom_components.at.core.manager import JobChange, JobManager
    from custom_components.at.data import AtConfigEntry


class AtEntity(Entity):
    """Base entity on the entry's single service device, updated whenever the job queue changes."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: AtConfigEntry, entity_description: EntityDescription) -> None:
        """Initialize the entity; its unique id is the entry id and the description key."""
        super().__init__()
        self.entity_description = entity_description
        self._manager: JobManager = entry.runtime_data.manager
        self._attr_unique_id = f"{entry.entry_id}_{entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=DISPLAY_NAME,
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        """Follow the job queue."""
        await super().async_added_to_hass()
        self.async_on_remove(self._manager.subscribe(self._on_change))

    @callback
    def _on_change(self, _change: JobChange) -> None:
        self.async_write_ha_state()
