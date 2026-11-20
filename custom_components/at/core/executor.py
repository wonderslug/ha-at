"""Run a due job: replay its intent or run its action."""

from typing import TYPE_CHECKING

import voluptuous as vol

from custom_components.at.const import DOMAIN
from custom_components.at.ha_internal.intents import async_run_intent
from custom_components.at.lang import get_language_pack, message
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

    def _message(self, key: str, **placeholders: object) -> str:
        return message(get_language_pack(self._hass.config.language), key, **placeholders)

    async def _context(self, job: Job) -> Context:
        """
        Build the context the job runs under.

        A job with no stored user runs with an empty context.

        Raises:
            JobExecutionError: The user who scheduled the job no longer exists.

        """
        user_id = job.source.user_id
        if user_id is None:
            return Context()
        if await self._hass.auth.async_get_user(user_id) is None:
            raise JobExecutionError(self._message("user_gone"))
        return Context(user_id=user_id)

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
            raise JobExecutionError(self._message("nothing_to_run"))
        await self._run_action(job, context)

    async def _run_action(self, job: Job, context: Context) -> None:
        action = job.action or []
        for entity_id in entity_ids_in(action):
            if self._hass.states.get(entity_id) is None:
                registered = er.async_get(self._hass).async_get(entity_id) is not None
                key = "entity_unavailable" if registered else "entity_gone"
                raise JobExecutionError(self._message(key, entity_id=entity_id))
        try:
            sequence = cv.SCRIPT_SCHEMA(action)
            await script.Script(self._hass, sequence, f"at job {job.id}", DOMAIN).async_run(context=context)
        except vol.Invalid as err:
            names = ", ".join(str(s.get("action")) for s in action if isinstance(s, dict) and s.get("action"))
            raise JobExecutionError(self._message("action_invalid", action=names or job.summary, error=err)) from err
        except HomeAssistantError as err:
            raise JobExecutionError(self._message("action_failed", summary=job.summary, error=err)) from err
