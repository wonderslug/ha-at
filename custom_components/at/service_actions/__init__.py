"""Service action registration for at."""

from typing import TYPE_CHECKING

from homeassistant.core import callback

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the integration's service actions once, at component level."""
