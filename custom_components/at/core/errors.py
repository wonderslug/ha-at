"""Errors raised by the job manager and executor."""

from homeassistant.exceptions import HomeAssistantError


class JobNotFound(HomeAssistantError):
    """No job has the given id."""


class JobStateError(HomeAssistantError):
    """The job is not in a state that allows the operation."""


class JobExecutionError(HomeAssistantError):
    """Running a job failed; the message is stored in ``result.error``."""

    def __init__(self, message: str) -> None:
        """Keep the message so the manager can record it."""
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        """Return the message."""
        return self.message
