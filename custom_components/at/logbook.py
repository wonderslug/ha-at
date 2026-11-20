"""Logbook descriptions for job events."""

from typing import TYPE_CHECKING

from homeassistant.core import callback
from homeassistant.util import dt as dt_util

from .const import (
    DISPLAY_NAME,
    DOMAIN,
    EVENT_JOB_CANCELLED,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_FAILED,
    EVENT_JOB_MISSED,
    EVENT_JOB_SCHEDULED,
)
from .lang import get_language_pack
from .lang.en import EN, format_clock

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from homeassistant.core import Event, HomeAssistant

_KEYS = {
    EVENT_JOB_SCHEDULED: "scheduled",
    EVENT_JOB_EXECUTED: "executed",
    EVENT_JOB_FAILED: "failed",
    EVENT_JOB_CANCELLED: "cancelled",
    EVENT_JOB_MISSED: "missed",
}


@callback
def async_describe_events(
    hass: HomeAssistant,
    async_describe_event: Callable[[str, str, Callable[[Event], dict[str, str]]], None],
) -> None:
    """Describe the job events for the logbook, in the language Home Assistant uses when each one is shown."""

    def describe(event: Event) -> dict[str, str]:
        pack = get_language_pack(hass.config.language) or EN
        key = _KEYS[str(event.event_type)]
        data = event.data
        values: dict[str, Any] = {"summary": data.get("summary", "")}
        if key == "scheduled":
            due = dt_util.parse_datetime(data["due"])
            values["time"] = format_clock(dt_util.as_local(due)) if due else data["due"]
        elif key == "failed":
            if data.get("error"):
                values["error"] = data["error"]
            else:
                key = "failed_no_error"
        return {"name": DISPLAY_NAME, "message": pack.logbook[key].format(**values)}

    for event_type in _KEYS:
        async_describe_event(DOMAIN, event_type, describe)
