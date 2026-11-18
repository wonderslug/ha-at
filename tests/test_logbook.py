"""Tests for logbook descriptions."""

from datetime import UTC, datetime
from typing import Any

from custom_components.at.const import (
    DISPLAY_NAME,
    DOMAIN,
    EVENT_JOB_CANCELLED,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_FAILED,
    EVENT_JOB_MISSED,
    EVENT_JOB_SCHEDULED,
)
from custom_components.at.lang.en import format_clock
from custom_components.at.logbook import async_describe_events
from homeassistant.core import Event, HomeAssistant

SUMMARY = "Turn on Porch Light"


def _describers(hass: HomeAssistant) -> dict[str, Any]:
    registered: dict[str, Any] = {}

    def register(domain: str, event_type: str, describe: Any) -> None:
        assert domain == DOMAIN
        registered[event_type] = describe

    async_describe_events(hass, register)
    return registered


def _event(event_type: str, **extra: str) -> Event:
    data = {
        "job_id": "abcd1234",
        "summary": SUMMARY,
        "due": datetime(2026, 11, 18, 7, 0, tzinfo=UTC).isoformat(),
        "status": "pending",
        "via": "voice",
        **extra,
    }
    return Event(event_type, data)


async def test_logbook_describes_events(hass: HomeAssistant) -> None:
    """Each job event gets the display name and its message."""
    await hass.config.async_set_time_zone("America/Los_Angeles")
    describers = _describers(hass)
    assert set(describers) == {
        EVENT_JOB_SCHEDULED,
        EVENT_JOB_EXECUTED,
        EVENT_JOB_FAILED,
        EVENT_JOB_CANCELLED,
        EVENT_JOB_MISSED,
    }
    expected = {
        EVENT_JOB_SCHEDULED: ("scheduled Turn on Porch Light for 11:00 PM", {}),
        EVENT_JOB_EXECUTED: ("ran Turn on Porch Light", {}),
        EVENT_JOB_FAILED: ("failed Turn on Porch Light: boom", {"error": "boom"}),
        EVENT_JOB_CANCELLED: ("cancelled Turn on Porch Light", {}),
        EVENT_JOB_MISSED: ("missed Turn on Porch Light (Home Assistant was down)", {}),
    }
    for event_type, (message, extra) in expected.items():
        assert describers[event_type](_event(event_type, **extra)) == {"name": DISPLAY_NAME, "message": message}


async def test_logbook_failed_without_error(hass: HomeAssistant) -> None:
    """A failed event with no error text still reads cleanly."""
    describers = _describers(hass)
    event = Event(EVENT_JOB_FAILED, {"summary": SUMMARY, "due": "2026-11-18T07:00:00+00:00", "error": None})
    assert describers[EVENT_JOB_FAILED](event)["message"] == "failed Turn on Porch Light"


def test_format_clock() -> None:
    """Twelve-hour clock with minutes kept."""
    assert format_clock(datetime(2026, 1, 1, 6, 30)) == "6:30 AM"
    assert format_clock(datetime(2026, 1, 1, 0, 5)) == "12:05 AM"
    assert format_clock(datetime(2026, 1, 1, 12, 0)) == "12:00 PM"
    assert format_clock(datetime(2026, 1, 1, 23, 0)) == "11:00 PM"
