"""The options form schema."""

from collections.abc import Mapping
from typing import Any

import probatio as vol

from custom_components.at.const import (
    CONF_DEFER_RELATIVE,
    CONF_GRACE_MINUTES,
    CONF_HISTORY_DAYS,
    CONF_HISTORY_MAX,
    CONF_PANEL_ADMIN_ONLY,
    DEFAULT_DEFER_RELATIVE,
    DEFAULT_GRACE_MINUTES,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_HISTORY_MAX,
    DEFAULT_PANEL_ADMIN_ONLY,
)
from homeassistant.helpers.selector import BooleanSelector, NumberSelector, NumberSelectorConfig, NumberSelectorMode


def _number(minimum: int, maximum: int) -> NumberSelector:
    return NumberSelector(NumberSelectorConfig(min=minimum, max=maximum, step=1, mode=NumberSelectorMode.BOX))


def options_schema(current: Mapping[str, Any]) -> vol.Schema:
    """
    Build the options form with the current values as defaults.

    Returns:
        The schema, defaulting to the stored options or the integration defaults.

    """
    return vol.Schema(
        {
            vol.Required(CONF_GRACE_MINUTES, default=current.get(CONF_GRACE_MINUTES, DEFAULT_GRACE_MINUTES)): vol.All(
                _number(0, 1440), vol.Coerce(int)
            ),
            vol.Required(CONF_HISTORY_DAYS, default=current.get(CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS)): vol.All(
                _number(1, 365), vol.Coerce(int)
            ),
            vol.Required(CONF_HISTORY_MAX, default=current.get(CONF_HISTORY_MAX, DEFAULT_HISTORY_MAX)): vol.All(
                _number(1, 10000), vol.Coerce(int)
            ),
            vol.Required(
                CONF_PANEL_ADMIN_ONLY, default=current.get(CONF_PANEL_ADMIN_ONLY, DEFAULT_PANEL_ADMIN_ONLY)
            ): BooleanSelector(),
            vol.Required(
                CONF_DEFER_RELATIVE, default=current.get(CONF_DEFER_RELATIVE, DEFAULT_DEFER_RELATIVE)
            ): BooleanSelector(),
        }
    )
