"""Constants for at."""

from datetime import timedelta
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

STORAGE_KEY = "at.jobs"
STORAGE_VERSION = 1
STORAGE_MINOR_VERSION = 1

SWEEP_INTERVAL = timedelta(minutes=1)

EVENT_JOB_CANCELLED = "at_job_cancelled"
EVENT_JOB_EXECUTED = "at_job_executed"
EVENT_JOB_FAILED = "at_job_failed"
EVENT_JOB_MISSED = "at_job_missed"
EVENT_JOB_SCHEDULED = "at_job_scheduled"
