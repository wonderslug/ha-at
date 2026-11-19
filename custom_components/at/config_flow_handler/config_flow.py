"""Config flow for at — a single confirm step, one instance only."""

from typing import Any

from custom_components.at.const import DISPLAY_NAME, DOMAIN
from homeassistant import config_entries

from .options_flow import AtOptionsFlow


class AtConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for at."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> AtOptionsFlow:
        """
        Return the options flow for this handler.

        Returns:
            The options flow instance.

        """
        return AtOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """
        Confirm the setup of the single instance.

        Returns:
            The confirm form, or the created config entry.

        """
        if user_input is None:
            return self.async_show_form(step_id="user")

        return self.async_create_entry(title=DISPLAY_NAME, data={})
