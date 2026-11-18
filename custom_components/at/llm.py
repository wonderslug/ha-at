"""Offer the at intents as tools of Home Assistant's LLM APIs (Assist)."""

from typing import override

from custom_components.at.const import DOMAIN
from custom_components.at.core.models import Via
from custom_components.at.voice.intents import AtCancelHandler, AtListHandler, AtScheduleHandler
from homeassistant.components.llm import LLMTools
from homeassistant.core import Context, HomeAssistant, callback
from homeassistant.helpers import intent, llm


class AtTool(llm.IntentTool):
    """
    An intent tool that calls its own handler.

    Home Assistant's IntentTool looks the handler up again by intent type, which finds the
    voice handler, so a job scheduled by a model would be recorded as spoken. Calling the
    handler the tool was built with keeps ``Via.LLM``. The tool result carries the speech.
    """

    def __init__(self, handler: intent.IntentHandler) -> None:
        """Name the tool ``at__<IntentType>``."""
        super().__init__(f"{DOMAIN}__{handler.intent_type}", handler, integration=DOMAIN)
        self._handler = handler

    @override
    async def async_call(
        self, hass: HomeAssistant, tool_input: llm.ToolInput, llm_context: llm.LLMContext
    ) -> llm.ToolResult:
        """Run the handler with the model's arguments as slots."""
        slots = {
            key: {"value": value}
            for key, value in tool_input.tool_args.items()
            if not intent.is_blank_slot_value(value)
        }
        intent_obj = intent.Intent(
            hass,
            platform=llm_context.platform,
            intent_type=self.intent_type,
            slots=slots,
            text_input=None,
            context=llm_context.context or Context(),
            language=llm_context.language or hass.config.language,
            assistant=llm_context.assistant,
            device_id=llm_context.device_id,
        )
        response = await self._handler.async_handle(intent_obj)
        return llm.ToolResult(data=llm.IntentResponseDict(response))


@callback
def async_get_tools(hass: HomeAssistant, llm_context: llm.LLMContext, api_id: str) -> LLMTools | None:
    """
    Return the three scheduling tools.

    Home Assistant does not offer a custom intent to an LLM by itself; this platform does.
    The handlers are built with ``Via.LLM`` so jobs record that a model scheduled them.
    """
    handlers = (AtScheduleHandler(via=Via.LLM), AtListHandler(via=Via.LLM), AtCancelHandler(via=Via.LLM))
    return LLMTools(tools=[AtTool(handler) for handler in handlers])
