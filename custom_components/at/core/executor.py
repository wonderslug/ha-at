"""Run a due job: replay its intent or run its action."""

from typing import TYPE_CHECKING

import voluptuous as vol

from custom_components.at.const import DOMAIN
from custom_components.at.ha_internal.intents import async_run_intent
from homeassistant.core import Context
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, entity_registry as er, script

from .actions import entity_ids_in
from .errors import JobExecutionError

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .models import Job


class JobExecutor:
    """Runs jobs for the manager."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Keep the Home Assistant instance."""
        self._hass = hass

    async def _context(self, job: Job) -> Context:
        """Run as the job's user if it still exists, otherwise as the system."""
        user_id = job.source.user_id
        if user_id and await self._hass.auth.async_get_user(user_id) is not None:
            return Context(user_id=user_id)
        return Context()

    async def async_execute(self, job: Job) -> None:
        """
        Run the job now.

        Raises:
            JobExecutionError: Running failed; the message names what went wrong.

        """
        context = await self._context(job)
        if job.intent is not None:
            await async_run_intent(self._hass, job.intent, context)
            return
        if not job.action:
            msg = "the job has nothing to run"
            raise JobExecutionError(msg)
        await self._run_action(job, context)

    async def _run_action(self, job: Job, context: Context) -> None:
        action = job.action or []
        for entity_id in entity_ids_in(action):
            if self._hass.states.get(entity_id) is None:
                registered = er.async_get(self._hass).async_get(entity_id) is not None
                msg = f"{entity_id} is unavailable" if registered else f"{entity_id} no longer exists"
                raise JobExecutionError(msg)
        try:
            sequence = cv.SCRIPT_SCHEMA(action)
            await script.Script(self._hass, sequence, f"at job {job.id}", DOMAIN).async_run(context=context)
        except vol.Invalid as err:
            msg = f"the stored action is invalid: {err}"
            raise JobExecutionError(msg) from err
        except HomeAssistantError as err:
            msg = f"{job.summary}: {err}"
            raise JobExecutionError(msg) from err
