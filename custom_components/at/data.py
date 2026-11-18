"""
Runtime data types for at.

Access pattern: entry.runtime_data.client / entry.runtime_data.coordinator
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import AtApiClient
    from .coordinator import AtDataUpdateCoordinator


type AtConfigEntry = ConfigEntry[AtData]


@dataclass
class AtData:
    """Runtime data stored on the config entry after a successful setup."""

    client: AtApiClient
    coordinator: AtDataUpdateCoordinator
    integration: Integration
