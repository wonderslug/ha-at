"""
Runtime data types for at.

Access pattern: entry.runtime_data (fields are added as features land).
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry


type AtConfigEntry = ConfigEntry[AtRuntimeData]


@dataclass
class AtRuntimeData:
    """Runtime data stored on the config entry after setup."""
