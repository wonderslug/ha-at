"""To-do platform for at."""

from typing import TYPE_CHECKING

from .scheduled import AtScheduledTodo

if TYPE_CHECKING:
    from custom_components.at.data import AtConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AtConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the to-do platform."""
    async_add_entities([AtScheduledTodo(entry)])
