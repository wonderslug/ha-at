"""Constants, helpers and stand-in agents shared by the voice tests and the `assist` fixture (tests/conftest.py)."""

from dataclasses import dataclass
from typing import override

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components import conversation
from homeassistant.components.assist_pipeline import (
    PipelineEvent,
    PipelineEventType,
    async_get_pipelines,
    async_update_pipeline,
)
from homeassistant.components.assist_pipeline.models import PipelineStage
from homeassistant.components.assist_pipeline.pipeline import async_get_pipeline
from homeassistant.components.assist_pipeline.run import PipelineInput, PipelineRun
from homeassistant.const import MATCH_ALL
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.helpers import chat_session, intent
from homeassistant.setup import async_setup_component

ASSISTANT = conversation.DOMAIN
LANGUAGE = "en"
LIGHT = "light.master_bathroom"
STUB_SPEECH = "stub agent"


@dataclass
class Assist:
    """What the voice tests share: a satellite in the office and two lights."""

    device_id: str
    turn_on_calls: list[ServiceCall]


async def say(hass: HomeAssistant, home: Assist, text: str) -> str:
    result = await conversation.async_converse(hass, text, None, Context(), LANGUAGE, device_id=home.device_id)
    return result.response.speech["plain"]["speech"]


class StubLlmAgent(conversation.AbstractConversationAgent):
    """A non-default agent standing in for an LLM; it records what reaches it."""

    def __init__(self) -> None:
        """Start with no calls."""
        self.texts: list[str] = []

    @property
    @override
    def supported_languages(self) -> list[str] | str:
        """Accept every language."""
        return MATCH_ALL

    @override
    async def async_process(self, user_input: conversation.ConversationInput) -> conversation.ConversationResult:
        """Answer every sentence with the same speech."""
        self.texts.append(user_input.text)
        response = intent.IntentResponse(language=user_input.language)
        response.async_set_speech(STUB_SPEECH)
        return conversation.ConversationResult(response=response, conversation_id=user_input.conversation_id)


async def use_agent(hass: HomeAssistant, agent: conversation.AbstractConversationAgent) -> str:
    """Make ``agent`` the pipeline's agent, with prefer-local on, and return its agent id."""
    assert await async_setup_component(hass, "assist_pipeline", {})
    agent_entry = MockConfigEntry(domain="test", title="Stub LLM")
    agent_entry.add_to_hass(hass)
    conversation.async_set_agent(hass, agent_entry, agent)
    (pipeline,) = async_get_pipelines(hass)
    await async_update_pipeline(hass, pipeline, conversation_engine=agent_entry.entry_id, prefer_local_intents=True)
    return agent_entry.entry_id


async def run_pipeline(hass: HomeAssistant, home: Assist, text: str) -> str:
    speech, _conversation_id = await run_pipeline_with_id(hass, home, text)
    return speech


async def run_pipeline_with_id(hass: HomeAssistant, home: Assist, text: str) -> tuple[str, str]:
    (pipeline,) = async_get_pipelines(hass)
    events: list[PipelineEvent] = []
    with chat_session.async_get_chat_session(hass) as session:
        conversation_id = session.conversation_id
        await PipelineInput(
            session=session,
            intent_input=text,
            device_id=home.device_id,
            run=PipelineRun(
                hass,
                context=Context(),
                pipeline=async_get_pipeline(hass, pipeline.id),
                start_stage=PipelineStage.INTENT,
                end_stage=PipelineStage.INTENT,
                event_callback=events.append,
            ),
        ).execute(validate=True)
    (intent_end,) = [event for event in events if event.type is PipelineEventType.INTENT_END]
    assert intent_end.data is not None
    return intent_end.data["intent_output"]["response"]["speech"]["plain"]["speech"], conversation_id
