"""Service action registration for at."""

from typing import TYPE_CHECKING, Any

import probatio

from custom_components.at.const import DOMAIN
from custom_components.at.core.models import JobStatus
from homeassistant.core import SupportsResponse, callback
from homeassistant.helpers import config_validation as cv

from .cancel import async_handle_cancel
from .clear_history import async_handle_clear_history
from .list import async_handle_list
from .run_now import async_handle_run_now
from .schedule import async_handle_schedule

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse

    type Handler = Callable[[HomeAssistant, ServiceCall], Awaitable[ServiceResponse]]

SERVICE_SCHEDULE = "schedule"
SERVICE_LIST = "list"
SERVICE_CANCEL = "cancel"
SERVICE_RUN_NOW = "run_now"
SERVICE_CLEAR_HISTORY = "clear_history"


def _exactly_one(keys: tuple[str, ...], message: str) -> Any:
    def check(data: dict[str, Any]) -> dict[str, Any]:
        if sum(key in data for key in keys) != 1:
            raise probatio.Invalid(message)
        return data

    return check


SCHEDULE_SCHEMA = probatio.All(
    probatio.Schema(
        {
            probatio.Exclusive("command", "what"): cv.string,
            probatio.Exclusive("action", "what"): cv.SCRIPT_SCHEMA,
            probatio.Exclusive("at", "when"): cv.datetime,
            probatio.Exclusive("delay", "when"): cv.positive_time_period,
            probatio.Exclusive("when", "when"): cv.string,
            probatio.Optional("name"): cv.string,
        }
    ),
    _exactly_one(("command", "action"), "provide exactly one of command or action"),
    _exactly_one(("at", "delay", "when"), "provide exactly one of at, delay or when"),
)

LIST_SCHEMA = probatio.Schema(
    {
        probatio.Optional("status"): [probatio.In([str(s) for s in JobStatus])],
        probatio.Optional("start"): cv.datetime,
        probatio.Optional("end"): cv.datetime,
    }
)

CANCEL_SCHEMA = probatio.All(
    probatio.Schema(
        {
            probatio.Exclusive("job_id", "which"): probatio.All(cv.ensure_list, [cv.string]),
            probatio.Exclusive("all", "which"): cv.boolean,
        }
    ),
    _exactly_one(("job_id", "all"), "provide exactly one of job_id or all"),
)

RUN_NOW_SCHEMA = probatio.Schema({probatio.Required("job_id"): cv.string})
CLEAR_HISTORY_SCHEMA = probatio.Schema({})


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the integration's service actions once, at component level."""
    registrations = (
        (SERVICE_SCHEDULE, async_handle_schedule, SCHEDULE_SCHEMA, SupportsResponse.OPTIONAL),
        (SERVICE_LIST, async_handle_list, LIST_SCHEMA, SupportsResponse.ONLY),
        (SERVICE_CANCEL, async_handle_cancel, CANCEL_SCHEMA, SupportsResponse.OPTIONAL),
        (SERVICE_RUN_NOW, async_handle_run_now, RUN_NOW_SCHEMA, SupportsResponse.NONE),
        (SERVICE_CLEAR_HISTORY, async_handle_clear_history, CLEAR_HISTORY_SCHEMA, SupportsResponse.OPTIONAL),
    )
    for name, handler, schema, supports_response in registrations:
        if hass.services.has_service(DOMAIN, name):
            continue

        async def call(service_call: ServiceCall, handler: Handler = handler) -> ServiceResponse:
            return await handler(hass, service_call)

        hass.services.async_register(DOMAIN, name, call, schema=schema, supports_response=supports_response)
