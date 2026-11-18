"""
Diagnostics support for at.

https://contributors.home-assistant.io/core/integrations/diagnostics/
"""

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.redact import async_redact_data

from .core.models import JobStatus
from .ha_internal import fallthrough, intents, recognize, sentence_triggers
from .lang import get_language_pack

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import AtConfigEntry

TO_REDACT = {"user_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: AtConfigEntry,
) -> dict[str, Any]:
    """
    Return diagnostics for a config entry.

    Job bodies are left out on purpose: only counts by status are reported.

    Returns:
        The redacted entry configuration, job counts, language support and adapter probes.

    """
    manager = entry.runtime_data.manager
    counts = dict.fromkeys((str(status) for status in JobStatus), 0)
    for job in [*manager.pending(), *manager.running(), *manager.history()]:
        counts[str(job.status)] += 1
    return async_redact_data(
        {
            "entry": {
                "version": entry.version,
                "minor_version": entry.minor_version,
                "state": str(entry.state),
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            "counts": counts,
            "language": hass.config.language,
            "language_supported": get_language_pack(hass.config.language) is not None,
            "ha_internal": {
                "recognize": recognize.probe(),
                "intents": intents.probe(),
                "sentence_triggers": sentence_triggers.probe(),
                "fallthrough": fallthrough.probe(),
            },
        },
        TO_REDACT,
    )
