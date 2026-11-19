"""Resolve the automation or script that issued a call, the way the logbook attributes it."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import Context, HomeAssistant

ORIGIN_DOMAINS = ("script", "automation")


def origin_entity_id(hass: HomeAssistant, context: Context | None) -> str | None:
    """Return the script or automation whose current run shares ``context``, if any.

    Automations and scripts write their state with the context their actions run under, so a call made from
    within a run carries the same context id as that entity's state. A script started by an automation shares
    the automation's context; the script is the closer origin, so scripts are checked first.
    """
    if context is None:
        return None
    for domain in ORIGIN_DOMAINS:
        for state in hass.states.async_all(domain):
            if state.context.id == context.id:
                return state.entity_id
    return None
