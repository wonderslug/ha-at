"""Options flow for at (stub; options are added later)."""

from typing import Any

from homeassistant import config_entries


class AtOptionsFlow(config_entries.OptionsFlowWithReload):
    """Options flow, currently an empty form."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """
        Show and process the options form.

        Returns:
            The empty form, or the stored options.

        """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init")


__all__ = ["AtOptionsFlow"]
