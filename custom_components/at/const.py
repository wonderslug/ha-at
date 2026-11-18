"""Constants for at."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "at"
DISPLAY_NAME = "at (placeholder)"

CONF_GRACE_MINUTES = "grace_minutes"
DEFAULT_GRACE_MINUTES = 5

CONF_HISTORY_DAYS = "history_days"
DEFAULT_HISTORY_DAYS = 7

CONF_HISTORY_MAX = "history_max"
DEFAULT_HISTORY_MAX = 100

CONF_PANEL_ADMIN_ONLY = "panel_admin_only"
DEFAULT_PANEL_ADMIN_ONLY = False

CONF_DEFER_RELATIVE = "defer_relative_to_ha"
DEFAULT_DEFER_RELATIVE = False
