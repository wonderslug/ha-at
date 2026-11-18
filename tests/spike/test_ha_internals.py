"""
Contract tests for the Home Assistant internals that the voice design of `at` rests on.

Each test proves one item of spec §10 against the real conversation, intent, llm,
assist_pipeline and panel_custom components. A failure here after a Home Assistant
upgrade means an adapter in `ha_internal/` needs attention; see
docs/development/SPIKE-FINDINGS.md for what each test relies on.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
import json
from typing import Any, override
from unittest.mock import Mock

from hassil import Intents, recognize_best
from hassil.recognize import RecognizeResult
import probatio
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service, mock_platform

from custom_components.at.const import DOMAIN
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
from homeassistant.components.conversation.agent_manager import get_agent_manager
from homeassistant.components.conversation.const import IntentSource
from homeassistant.components.conversation.default_agent import DefaultAgent
from homeassistant.components.frontend import DATA_PANELS
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.components.llm import LLMTools
from homeassistant.components.panel_custom import async_register_panel
from homeassistant.const import ATTR_FRIENDLY_NAME, MATCH_ALL
from homeassistant.core import CALLBACK_TYPE, Context, HomeAssistant, ServiceCall
from homeassistant.helpers import (
    area_registry as ar,
    chat_session,
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
    intent,
    llm,
)
from homeassistant.loader import async_get_integration
from homeassistant.setup import async_setup_component

# Home Assistant's http component stores plain string keys on its aiohttp app, which the
# project-wide "warnings are errors" filter would turn into a failed http setup.
pytestmark = [
    pytest.mark.real_dependencies,
    pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning"),
]

ASSISTANT = conversation.DOMAIN
LANGUAGE = "en"
AT_SENTENCES = ["at {hour} {command}", "{command} at {hour}"]
AT_LISTS = {"hour": {"range": {"from": 1, "to": 12}}}
TriggerCallback = Callable[[conversation.ConversationInput, RecognizeResult], Any]


@dataclass
class Assist:
    """What the voice tests share: a satellite in the office and two lights."""

    device_id: str
    turn_on_calls: list[ServiceCall]


@dataclass
class TriggerHits:
    """Slots seen by a sentence-trigger callback."""

    slots: list[dict[str, Any]] = field(default_factory=list)

    async def __call__(self, user_input: conversation.ConversationInput, result: RecognizeResult) -> str:
        """Record the slots and answer like the `at` callback would."""
        self.slots.append({name: entity.value for name, entity in result.entities.items()})
        return "Scheduled"


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
        response.async_set_speech("stub agent")
        return conversation.ConversationResult(response=response, conversation_id=user_input.conversation_id)


class AtScheduleHandler(intent.IntentHandler):
    """Placeholder for the real AtSchedule intent handler."""

    intent_type = "AtSchedule"
    description = "Schedules a Home Assistant command to run once at a later time."

    @property
    @override
    def slot_schema(self) -> dict | None:
        """Ask for the command and when to run it."""
        return {probatio.Required("command"): cv.string, probatio.Required("when"): cv.string}

    @override
    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Do nothing."""
        return intent_obj.create_response()


def register_at_trigger(
    hass: HomeAssistant,
    sentences: list[str],
    lists: dict[str, dict[str, Any]],
    trigger_callback: TriggerCallback,
) -> CALLBACK_TYPE:
    """
    Register sentence triggers on the default agent, with real slot lists.

    `AgentManager.register_trigger` treats every `{slot}` as a wildcard. Slot lists set on
    the trigger's intent data take precedence over those wildcards in hassil, so the
    lists are added to the data block that `register_trigger` just stored. The default
    agent rebuilds its trigger intents lazily on the next sentence, so this runs before
    any recognition can see the trigger without its lists.

    Returns:
        The callback that unregisters the trigger.

    """
    manager = get_agent_manager(hass)
    unregister = manager.register_trigger(sentences=sentences, trigger_callback=trigger_callback)

    live: dict[IntentSource, dict[str, Any]] = {}
    manager.subscribe_intents(live.update)()
    (data,) = [
        data
        for trigger_intent in live[IntentSource.TRIGGER]["intents"].values()
        for data in trigger_intent["data"]
        if data["sentences"] is sentences
    ]
    data["lists"] = lists
    return unregister


def default_agent(hass: HomeAssistant) -> DefaultAgent:
    """Return Home Assistant's own conversation agent."""
    agent = get_agent_manager(hass).default_agent
    assert agent is not None
    return agent


def user_input(text: str, device_id: str | None) -> conversation.ConversationInput:
    """Build the conversation input a satellite would send."""
    return conversation.ConversationInput(
        text=text,
        context=Context(),
        conversation_id=None,
        device_id=device_id,
        satellite_id=None,
        language=LANGUAGE,
        agent_id=conversation.HOME_ASSISTANT_AGENT,
    )


@pytest.fixture
async def assist(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> Assist:
    """Set up the real conversation stack with an exposed and an unexposed light."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "conversation", {})
    assert await async_setup_component(hass, "intent", {})

    office = area_registry.async_create("Office")
    satellite_entry = MockConfigEntry(domain="test")
    satellite_entry.add_to_hass(hass)
    satellite = device_registry.async_get_or_create(
        config_entry_id=satellite_entry.entry_id, identifiers={("test", "satellite")}
    )
    device_registry.async_update_device(satellite.id, area_id=office.id)

    for object_id, name, exposed in (("kitchen", "Kitchen light", True), ("garage", "Garage light", False)):
        entry = entity_registry.async_get_or_create(
            "light", "test", object_id, suggested_object_id=object_id, original_name=name
        )
        hass.states.async_set(entry.entity_id, "off", {ATTR_FRIENDLY_NAME: name})
        async_expose_entity(hass, ASSISTANT, entry.entity_id, exposed)

    turn_on_calls = async_mock_service(hass, "light", "turn_on")
    await hass.async_block_till_done()
    return Assist(device_id=satellite.id, turn_on_calls=turn_on_calls)


async def test_programmatic_sentence_trigger_wildcard_both_orders(hass: HomeAssistant, assist: Assist) -> None:
    """Item 1: triggers with a range-list hour and a wildcard command match in both word orders."""
    hits = TriggerHits()
    unregister = register_at_trigger(hass, AT_SENTENCES, AT_LISTS, hits)

    for text in (
        "at 11 turn on the kitchen light",
        "turn on the kitchen light at 11",
        "at eleven turn on the kitchen light",
    ):
        result = await conversation.async_converse(hass, text, None, Context(), LANGUAGE, device_id=assist.device_id)
        assert result.response.speech["plain"]["speech"] == "Scheduled"

    assert [hit["command"] for hit in hits.slots] == ["turn on the kitchen light"] * 3
    assert [int(hit["hour"]) for hit in hits.slots] == [11, 11, 11]
    assert hass.states.get("light.kitchen").state == "off"
    assert assist.turn_on_calls == []

    # An hour outside the range list is not an `at` sentence, so Assist handles it as usual.
    await conversation.async_converse(hass, "turn on the kitchen light at 13", None, Context(), LANGUAGE)
    assert len(hits.slots) == 3

    unregister()
    await conversation.async_converse(hass, "at 11 turn on the kitchen light", None, Context(), LANGUAGE)
    assert len(hits.slots) == 3


async def test_trigger_with_literal_hours_uses_only_public_api(hass: HomeAssistant, assist: Assist) -> None:
    """Fallback for item 1: literal hour alternatives, with `at` re-parsing the time itself."""
    hours = "|".join(str(hour) for hour in range(1, 13))
    own_parser = Intents.from_dict(
        {
            "language": LANGUAGE,
            "intents": {"AtSchedule": {"data": [{"sentences": AT_SENTENCES}]}},
            "lists": {**AT_LISTS, "command": {"wildcard": True}},
        }
    )
    parsed: list[dict[str, Any]] = []

    async def on_trigger(conversation_input: conversation.ConversationInput, result: RecognizeResult) -> str:
        match = recognize_best(conversation_input.text, own_parser)
        assert match is not None
        parsed.append({name: entity.value for name, entity in match.entities.items()})
        return "Scheduled"

    # Every {slot} in a trigger is a wildcard, and hassil cannot split two adjacent wildcards,
    # so the hour is literal text in the trigger.
    get_agent_manager(hass).register_trigger(
        sentences=[f"at ({hours}) {{command}}", f"{{command}} at ({hours})"], trigger_callback=on_trigger
    )

    for text in ("at 11 turn on the kitchen light", "turn on the kitchen light at 11"):
        await conversation.async_converse(hass, text, None, Context(), LANGUAGE)

    assert [(int(slots["hour"]), slots["command"]) for slots in parsed] == [(11, "turn on the kitchen light")] * 2
    assert assist.turn_on_calls == []


async def test_recognize_only_returns_intent_without_executing(hass: HomeAssistant, assist: Assist) -> None:
    """Item 2: recognition gives the intent and slots, runs nothing, and tells the failures apart."""
    agent = default_agent(hass)

    exposed = await agent.async_recognize_intent(user_input("turn on the kitchen light", assist.device_id))
    assert exposed is not None
    assert exposed.intent.name == intent.INTENT_TURN_ON
    assert exposed.entities["name"].value == "Kitchen light"
    assert not exposed.unmatched_entities
    assert hass.states.get("light.kitchen").state == "off"
    assert assist.turn_on_calls == []

    # Not exposed: recognized like any other name; the target check below tells it apart.
    unexposed = await agent.async_recognize_intent(user_input("turn on the garage light", assist.device_id))
    assert unexposed is not None
    assert unexposed.intent.name == intent.INTENT_TURN_ON
    assert not unexposed.unmatched_entities

    # Unknown name: the best guess carries the unmatched name.
    unknown = await agent.async_recognize_intent(user_input("turn on the zzz light", assist.device_id))
    assert unknown is not None
    assert unknown.intent.name == intent.INTENT_TURN_ON
    assert unknown.unmatched_entities["name"].text.strip() == "zzz"

    # No intent at all.
    assert await agent.async_recognize_intent(user_input("sing me a song about turnips", assist.device_id)) is None

    # The target check the intent handler will make at run time, without running it.
    for name, matched, reason in (
        ("Kitchen light", True, None),
        ("Garage light", False, intent.MatchFailedReason.ASSISTANT),
        ("zzz light", False, intent.MatchFailedReason.NAME),
    ):
        targets = intent.async_match_targets(
            hass, intent.MatchTargetsConstraints(name=name, domains={"light"}, assistant=ASSISTANT)
        )
        assert (targets.is_match, targets.no_match_reason) == (matched, reason)
    assert assist.turn_on_calls == []


async def test_run_stored_intent_later(hass: HomeAssistant, assist: Assist) -> None:
    """Item 3: a recognized intent survives JSON and runs later with exposure checked again."""
    sentence = "turn on the kitchen light"
    recognized = await default_agent(hass).async_recognize_intent(user_input(sentence, assist.device_id))
    assert recognized is not None
    stored = json.dumps(
        {
            "intent_type": recognized.intent.name,
            "slots": {entity.name: {"value": entity.value, "text": entity.text} for entity in recognized.entities_list},
        }
    )

    async def run_stored() -> intent.IntentResponse:
        job = json.loads(stored)
        return await intent.async_handle(
            hass,
            conversation.DOMAIN,
            job["intent_type"],
            job["slots"],
            sentence,
            Context(),
            LANGUAGE,
            assistant=ASSISTANT,
            device_id=assist.device_id,
        )

    response = await run_stored()
    assert response.response_type is intent.IntentResponseType.ACTION_DONE
    assert [call.data["entity_id"] for call in assist.turn_on_calls] == [["light.kitchen"]]

    async_expose_entity(hass, ASSISTANT, "light.kitchen", False)
    with pytest.raises(intent.MatchFailedError) as failure:
        await run_stored()
    assert failure.value.result.no_match_reason is intent.MatchFailedReason.ASSISTANT
    assert len(assist.turn_on_calls) == 1


async def test_custom_intent_offered_to_llm_api(hass: HomeAssistant, assist: Assist) -> None:
    """Item 4: a registered intent is an LLM tool only once the integration's `llm` platform offers it."""
    handler = AtScheduleHandler()
    intent.async_register(hass, handler)
    llm_context = llm.LLMContext(
        platform="test", context=Context(), language=LANGUAGE, assistant=ASSISTANT, device_id=assist.device_id
    )

    api = await llm.async_get_api(hass, llm.LLM_API_ASSIST, llm_context)
    assert [tool.name for tool in api.tools if getattr(tool, "intent_type", None) == handler.intent_type] == []

    def async_get_tools(hass: HomeAssistant, llm_context: llm.LLMContext, api_id: str) -> LLMTools | None:
        return LLMTools(tools=[llm.IntentTool(f"{DOMAIN}__{handler.intent_type}", handler, integration=DOMAIN)])

    await async_get_integration(hass, DOMAIN)
    mock_platform(hass, f"{DOMAIN}.llm", Mock(spec=["async_get_tools"], async_get_tools=async_get_tools))
    hass.config.components.add(DOMAIN)

    api = await llm.async_get_api(hass, llm.LLM_API_ASSIST, llm_context)
    tools = {tool.name: tool for tool in api.tools}
    assert "at__AtSchedule" in tools
    assert tools["at__AtSchedule"].description == handler.description
    assert api.custom_serializer is not None

    result = await api.async_call_tool(
        llm.ToolInput(tool_name="at__AtSchedule", tool_args={"command": "turn on the kitchen light", "when": "at 11"})
    )
    assert result.data["response_type"] == "action_done"


@pytest.mark.parametrize(
    "prefer_local_intents", [pytest.param(True, id="prefer_local"), pytest.param(False, id="llm_only")]
)
async def test_sentence_trigger_fires_with_prefer_local_llm_pipeline(
    hass: HomeAssistant, assist: Assist, prefer_local_intents: bool
) -> None:
    """Item 5: a pipeline whose agent is not the default one still runs the `at` trigger first."""
    assert await async_setup_component(hass, "assist_pipeline", {})
    stub_agent = StubLlmAgent()
    agent_entry = MockConfigEntry(domain="test", title="Stub LLM")
    agent_entry.add_to_hass(hass)
    conversation.async_set_agent(hass, agent_entry, stub_agent)

    (pipeline,) = async_get_pipelines(hass)
    await async_update_pipeline(
        hass, pipeline, conversation_engine=agent_entry.entry_id, prefer_local_intents=prefer_local_intents
    )
    pipeline = async_get_pipeline(hass, pipeline.id)
    hits = TriggerHits()
    register_at_trigger(hass, AT_SENTENCES, AT_LISTS, hits)
    events: list[PipelineEvent] = []

    with chat_session.async_get_chat_session(hass) as session:
        await PipelineInput(
            session=session,
            intent_input="at 11 turn on the kitchen light",
            device_id=assist.device_id,
            run=PipelineRun(
                hass,
                context=Context(),
                pipeline=pipeline,
                start_stage=PipelineStage.INTENT,
                end_stage=PipelineStage.INTENT,
                event_callback=events.append,
            ),
        ).execute(validate=True)

    assert [hit["command"] for hit in hits.slots] == ["turn on the kitchen light"]
    assert stub_agent.texts == []
    assert assist.turn_on_calls == []
    (intent_end,) = [event for event in events if event.type is PipelineEventType.INTENT_END]
    assert intent_end.data is not None
    assert intent_end.data["processed_locally"] is True
    assert intent_end.data["intent_output"]["response"]["speech"]["plain"]["speech"] == "Scheduled"


async def test_panel_custom_registers(hass: HomeAssistant) -> None:
    """Item 6: a custom integration can add the `at` sidebar panel through panel_custom."""
    assert await async_setup_component(hass, "panel_custom", {})

    await async_register_panel(
        hass,
        frontend_url_path=DOMAIN,
        webcomponent_name="at-panel",
        sidebar_title="At",
        sidebar_icon="mdi:clock-outline",
        module_url="/at_static/at-panel.js",
        require_admin=False,
    )

    panel = hass.data[DATA_PANELS][DOMAIN]
    assert panel.to_response()["config"]["_panel_custom"]["name"] == "at-panel"
    assert panel.sidebar_title == "At"
