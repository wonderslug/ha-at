"""
Runtime data types for at.

Access pattern: entry.runtime_data (fields are added as features land).
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .core.manager import JobManager


type AtConfigEntry = ConfigEntry[AtRuntimeData]


@dataclass
class AtRuntimeData:
    """Runtime data stored on the config entry after setup."""

    manager: JobManager
    unregister_voice: Callable[[], None] = field(default=lambda: None)
