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

Both run in a fresh, isolated chat session. The trigger runs inside the pipeline's live chat
log, which at that moment ends in the default agent's unanswered ``trigger_sentence`` tool
call and has the pipeline's streaming listener attached. Reusing it would send an LLM a
history its API rejects, store that broken history for later turns, and stream the reply into
a pipeline that never closes the stream. ``async_get_chat_session`` and ``async_get_chat_log``
reuse whatever their context variables hold, so the hand-off runs as a task in a copied
context with both cleared.

Trade-off: the forwarded exchange starts a new conversation. The LLM doesn't see the earlier
turns of the user's conversation, and its reply isn't added to them.
"""

import asyncio
from collections.abc import Coroutine
import contextvars
from typing import TYPE_CHECKING, Any

from custom_components.at.const import LOGGER, REFUSED_INTENT_PREFIX
from homeassistant.components import conversation
from homeassistant.helpers import chat_session

# Private: the pipeline's active chat log. Without it the hand-off is still isolated, because
# it always uses a fresh conversation id and async_get_chat_log only reuses a log whose id
# matches, so a rename in Home Assistant must not stop the integration from loading.
try:
    from homeassistant.components.conversation.chat_log import current_chat_log
except ImportError:  # pragma: no cover - depends on the Home Assistant version
    current_chat_log = None

# Semi-private: only the wording of a no-match answer depends on it.
try:
    from homeassistant.components.conversation.agent_manager import get_agent_manager
except ImportError:  # pragma: no cover - depends on the Home Assistant version
    get_agent_manager = None

if TYPE_CHECKING:
    from hassil.recognize import RecognizeResult

    from custom_components.at.ha_internal.sentence_triggers import TriggerInput
    from homeassistant.core import HomeAssistant


def _speech(response: object) -> str:
    speech = getattr(response, "speech", {})
    return str(speech.get("plain", {}).get("speech", ""))


def _is_at_intent(result: RecognizeResult) -> bool:
    return result.intent.name.startswith(REFUSED_INTENT_PREFIX)


_NO_INTENT_KEY = "no_intent"
_warned_missing: set[str] = set()


def _clear(context: contextvars.Context, name: str, variable: contextvars.ContextVar[Any] | None) -> None:
    if variable is None:
        if name not in _warned_missing:
            _warned_missing.add(name)
            LOGGER.debug("Home Assistant has no %s context variable; relying on a fresh conversation id", name)
        return
    context.run(variable.set, None)


async def _isolated[T](coro: Coroutine[Any, Any, T]) -> T:
    """Run ``coro`` with no active chat session or chat log, without touching the caller's."""
    context = contextvars.copy_context()
    _clear(context, "current_session", getattr(chat_session, "current_session", None))
    _clear(context, "current_chat_log", current_chat_log)
    return await asyncio.get_running_loop().create_task(coro, context=context)


async def _async_forward(hass: HomeAssistant, given: TriggerInput) -> str:
    result = await conversation.async_converse(
        hass,
        given.sentence,
        None,
        given.context,
        given.language,
        agent_id=given.agent_id,
        device_id=given.device_id,
        satellite_id=given.satellite_id,
    )
    return _speech(result.response)


async def _async_default_intents(hass: HomeAssistant, given: TriggerInput) -> str | None:
    with chat_session.async_get_chat_session(hass) as session:
        user_input = conversation.ConversationInput(
            text=given.sentence,
            context=given.context,
            conversation_id=session.conversation_id,
            device_id=given.device_id,
            satellite_id=given.satellite_id,
            language=given.language,
            agent_id=conversation.HOME_ASSISTANT_AGENT,
        )
        with conversation.async_get_chat_log(hass, session, user_input) as chat_log:
            response = await conversation.async_handle_intents(hass, user_input, chat_log, intent_filter=_is_at_intent)
    return None if response is None else _speech(response)


def is_built_in_agent(agent_id: str | None) -> bool:
    """Say whether a sentence was meant for Home Assistant's built-in agent rather than another one, such as an LLM."""
    return agent_id is None or agent_id == conversation.HOME_ASSISTANT_AGENT


async def async_hand_off(hass: HomeAssistant, given: TriggerInput) -> str | None:
    """
    Answer the full sentence the way its agent would have without `at`.

    Returns:
        The agent's speech, or None when the built-in agent has no intent for the sentence.

    """
    if not is_built_in_agent(given.agent_id):
        return await _isolated(_async_forward(hass, given))
    return await _isolated(_async_default_intents(hass, given))


async def async_no_intent_speech(hass: HomeAssistant, language: str) -> str | None:
    """
    Return the built-in agent's own "didn't understand" sentence for ``language``.

    Returns:
        The sentence, or None when the agent or its sentences for that language are missing.

    """
    agent = None if get_agent_manager is None else get_agent_manager(hass).default_agent
    if agent is None or (lang_intents := await agent.async_get_or_load_intents(language)) is None:
        return None
    text = lang_intents.error_responses.get(_NO_INTENT_KEY)
    return str(text) if text else None


def probe() -> dict[str, bool]:
    """Report whether the private Home Assistant hooks this adapter uses resolved."""
    return {
        "current_chat_log": current_chat_log is not None,
        "current_session": hasattr(chat_session, "current_session"),
        "async_handle_intents": hasattr(conversation, "async_handle_intents"),
        "async_get_chat_log": hasattr(conversation, "async_get_chat_log"),
        "get_agent_manager": callable(get_agent_manager),
    }
