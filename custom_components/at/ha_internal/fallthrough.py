"""
Hand a sentence that `at` matched but can't schedule back to the agent it was meant for.

A matched sentence trigger takes the sentence away from the agent for good, and a callback
that answers None only makes Home Assistant say "Done". So when the command part isn't
something Assist knows ("remind me at 5", "broadcast dinner is at 6"), `at` passes the full
sentence on itself:

- to the pipeline's own agent when that isn't the built-in one (an LLM). Non-default agents
  don't run sentence triggers, so this can't loop back into `at`;
- otherwise to the built-in agent's intent matching, without its sentence triggers, so
  Home Assistant answers with its own response.
"""

from typing import TYPE_CHECKING

from custom_components.at.const import REFUSED_INTENT_PREFIX
from homeassistant.components import conversation
from homeassistant.helpers import chat_session

if TYPE_CHECKING:
    from hassil.recognize import RecognizeResult

    from custom_components.at.ha_internal.sentence_triggers import TriggerInput
    from homeassistant.core import HomeAssistant


def _speech(response: object) -> str:
    speech = getattr(response, "speech", {})
    return str(speech.get("plain", {}).get("speech", ""))


def _is_at_intent(result: RecognizeResult) -> bool:
    return result.intent.name.startswith(REFUSED_INTENT_PREFIX)


async def async_hand_off(hass: HomeAssistant, given: TriggerInput) -> str | None:
    """
    Answer the full sentence the way its agent would have without `at`.

    Returns:
        The agent's speech, or None when the built-in agent has no intent for the sentence.

    """
    if given.agent_id is not None and given.agent_id != conversation.HOME_ASSISTANT_AGENT:
        result = await conversation.async_converse(
            hass,
            given.sentence,
            given.conversation_id,
            given.context,
            given.language,
            agent_id=given.agent_id,
            device_id=given.device_id,
            satellite_id=given.satellite_id,
        )
        return _speech(result.response)

    user_input = conversation.ConversationInput(
        text=given.sentence,
        context=given.context,
        conversation_id=given.conversation_id,
        device_id=given.device_id,
        satellite_id=given.satellite_id,
        language=given.language,
        agent_id=conversation.HOME_ASSISTANT_AGENT,
    )
    with (
        chat_session.async_get_chat_session(hass, given.conversation_id) as session,
        conversation.async_get_chat_log(hass, session, user_input) as chat_log,
    ):
        response = await conversation.async_handle_intents(hass, user_input, chat_log, intent_filter=_is_at_intent)
    return None if response is None else _speech(response)
