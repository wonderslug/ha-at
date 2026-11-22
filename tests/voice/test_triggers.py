"""Sentence triggers on the built-in agent: schedule, list and cancel by voice."""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import replace
from typing import override
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.at.const import CONF_DEFER_RELATIVE
from custom_components.at.core.manager import JobManager
from custom_components.at.ha_internal.fallthrough import async_hand_off
from custom_components.at.ha_internal.sentence_triggers import LanguageSentences, TriggerInput, _gate_lists
from custom_components.at.lang.en import EN
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
from homeassistant.components.assist_satellite.const import AssistSatelliteEntityFeature
from homeassistant.components.conversation.chat_log import current_chat_log
from homeassistant.components.conversation.trigger import has_no_punctuation, is_valid_sentence
from homeassistant.const import MATCH_ALL
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.helpers import chat_session, entity_registry as er, intent
from homeassistant.setup import async_setup_component
from tests.assist import LIGHT, Assist, say  # noqa: TID251  (plain module; see tests/assist.py)

pytestmark = [
    pytest.mark.real_dependencies,
    pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning"),
]

UNRECOGNIZED = (
    "Sorry, I can only schedule commands I can check right now. Try rephrasing, or schedule a script or scene."
)


@pytest.fixture
def script_calls(hass: HomeAssistant) -> list[ServiceCall]:
    """Record script runs instead of running them."""
    return async_mock_service(hass, "script", "turn_on")


def bathroom_light_untouched(hass: HomeAssistant, home: Assist) -> bool:
    return hass.states.get(LIGHT).state == "off" and not [
        call for call in home.turn_on_calls if call.data.get("entity_id") in (LIGHT, [LIGHT])
    ]


@pytest.mark.parametrize(
    "sentence",
    [
        "at 11pm turn on the master bathroom light",
        "turn on the master bathroom light at 6am",
        "at 6:30 tonight turn on the master bathroom light",
        "tomorrow at 7 turn on the master bathroom light",
        "turn on the master bathroom light tomorrow at 7",
        "on friday at 8 turn on the master bathroom light",
        "in 30 minutes run the bedtime script",
        "run the bedtime script in 30 minutes",
        "in an hour and a half turn on the master bathroom light",
        "in forty five minutes run the bedtime script",
        "run the bedtime script in one hundred and twenty minutes",
        "turn on the master bathroom light at seven thirty",
        "at six forty five pm turn on the master bathroom light",
        "tomorrow at seven oh five turn on the master bathroom light",
    ],
)
async def test_schedule_sentences(
    hass: HomeAssistant, home: Assist, manager: JobManager, script_calls: list[ServiceCall], sentence: str
) -> None:
    speech = await say(hass, home, sentence)

    assert speech.startswith("OK, "), speech
    assert len(manager.pending()) == 1
    assert bathroom_light_untouched(hass, home)
    assert script_calls == []


@pytest.mark.parametrize(
    ("sentence", "expected"),
    [
        pytest.param("at 11pm turn on the master bathroom light", "OK, at 11 PM I'll turn on", id="absolute-first"),
        pytest.param("at 6:30 tonight turn on the master bathroom light", "OK, at 6:30 PM tomorrow", id="tonight"),
        pytest.param("turn on the master bathroom light tomorrow at 7", "OK, at 7 AM tomorrow", id="tomorrow-last"),
        pytest.param("on friday at 8 turn on the master bathroom light", "OK, at 8 AM on Friday", id="weekday"),
        pytest.param(
            "run the bedtime script in 30 minutes",
            "OK, in 30 minutes, at 10:52 PM, I'll run Bedtime",
            id="relative-last",
        ),
        pytest.param(
            "in an hour and a half turn on the master bathroom light",
            "OK, in 1 hour and 30 minutes",
            id="hour-and-a-half",
        ),
        pytest.param("turn on the master bathroom light at 1800 hours", "OK, at 6 PM tomorrow", id="hhmm-hours"),
        pytest.param("at eighteen hundred hours turn on the master bathroom light", "OK, at 6 PM", id="hundred-hours"),
        pytest.param("turn on the master bathroom light at 18 hundred", "OK, at 6 PM", id="digits-hundred"),
        pytest.param("at oh six hundred turn on the master bathroom light", "OK, at 6 AM tomorrow", id="oh-hundred"),
        pytest.param("turn on the master bathroom light at 23:15 hours", "OK, at 11:15 PM I'll", id="colon-hours"),
        pytest.param(
            "turn on the master bathroom light at twenty three fifteen hours", "OK, at 11:15 PM", id="words-hours"
        ),
    ],
)
async def test_time_and_command_are_split_cleanly(
    hass: HomeAssistant, home: Assist, manager: JobManager, sentence: str, expected: str
) -> None:
    speech = await say(hass, home, sentence)

    assert speech.startswith(expected), speech
    assert speech.endswith(("Master Bathroom Light.", "Bedtime.")), speech


@pytest.mark.parametrize(
    "sentence",
    [
        "set the master bathroom light brightness at 20",
        "turn on the master bathroom light at 18",
        "turn on the master bathroom light at twenty",
        "turn on the master bathroom light at 1800",
    ],
)
async def test_bare_hour_after_12_is_refused_not_run_now(
    hass: HomeAssistant, home: Assist, manager: JobManager, sentence: str
) -> None:
    speech = await say(hass, home, sentence)

    assert speech == "Sorry, I didn't understand when."
    assert manager.pending() == []
    assert bathroom_light_untouched(hass, home)


async def test_command_with_numbers_keeps_its_words(hass: HomeAssistant, home: Assist, manager: JobManager) -> None:
    speech = await say(hass, home, "set the master bathroom light to 50 percent at 6pm")

    assert speech.startswith("OK, at 6 PM tomorrow"), speech
    (job,) = manager.pending()
    assert job.original_text == "set the master bathroom light to 50 percent"
    assert bathroom_light_untouched(hass, home)


@pytest.mark.parametrize(
    "sentence",
    [
        pytest.param("turn on the master bathroom light", id="no-time"),
        pytest.param("turn on the master bathroom light at home", id="not-an-hour"),
        pytest.param("turn on the master bathroom light at 31", id="hour-out-of-range"),
    ],
)
async def test_plain_commands_are_left_to_assist(
    hass: HomeAssistant, home: Assist, manager: JobManager, sentence: str
) -> None:
    await say(hass, home, sentence)

    assert manager.pending() == []


async def test_plain_command_still_runs(hass: HomeAssistant, home: Assist, manager: JobManager) -> None:
    await say(hass, home, "turn on the master bathroom light")

    assert [call.data["entity_id"] for call in home.turn_on_calls] == [[LIGHT]]


async def schedule_three(hass: HomeAssistant, home: Assist) -> None:
    for sentence in (
        "at 11pm turn on the master bathroom light",
        "run the bedtime script in 30 minutes",
        "tomorrow at 7 turn on the master bathroom light",
    ):
        assert (await say(hass, home, sentence)).startswith("OK, ")


@pytest.mark.parametrize(
    ("sentence", "expected"),
    [
        ("what's scheduled", "3 scheduled: run Bedtime at 10:52 PM; turn on Master Bathroom Light at 11 PM; "),
        ("what is scheduled", "3 scheduled: run Bedtime at 10:52 PM; turn on Master Bathroom Light at 11 PM; "),
        (
            "what's scheduled for tonight",
            "2 scheduled: run Bedtime at 10:52 PM; turn on Master Bathroom Light at 11 PM.",
        ),
        ("what's scheduled for tomorrow", "1 scheduled: turn on Master Bathroom Light at 7 AM tomorrow."),
        (
            "what's scheduled for the master bathroom light",
            "2 scheduled: turn on Master Bathroom Light at 11 PM; turn on Master Bathroom Light at 7 AM tomorrow.",
        ),
    ],
)
async def test_list_sentences(
    hass: HomeAssistant, home: Assist, manager: JobManager, sentence: str, expected: str
) -> None:
    await schedule_three(hass, home)

    speech = await say(hass, home, sentence)

    assert speech.startswith(expected), speech
    assert len(manager.pending()) == 3


@pytest.mark.parametrize(
    ("sentence", "expected", "left"),
    [
        ("cancel the 6am job", "Cancelled: turn on Master Bathroom Light at 6 AM", ["Run Bedtime"]),
        ("cancel the job at 6", "Cancelled: turn on Master Bathroom Light at 6 AM", ["Run Bedtime"]),
        ("cancel the master bathroom light", "Cancelled: turn on Master Bathroom Light at 6 AM", ["Run Bedtime"]),
        ("cancel the bedtime script", "Cancelled: run Bedtime at 10:52 PM", ["Turn on Master Bathroom Light"]),
        ("cancel everything scheduled", "Cancelled 2 jobs.", []),
        ("cancel all jobs", "Cancelled 2 jobs.", []),
    ],
)
async def test_cancel_sentences(
    hass: HomeAssistant, home: Assist, manager: JobManager, sentence: str, expected: str, left: list[str]
) -> None:
    for scheduled in ("turn on the master bathroom light at 6am", "run the bedtime script in 30 minutes"):
        assert (await say(hass, home, scheduled)).startswith("OK, ")

    speech = await say(hass, home, sentence)

    assert speech.startswith(expected), speech
    assert [job.summary for job in manager.pending()] == left


@pytest.mark.parametrize("advice", ["cancel the 6 AM job tomorrow", "cancel the job at 6 tomorrow"])
async def test_cancel_same_time_on_two_days(
    hass: HomeAssistant, home: Assist, manager: JobManager, advice: str
) -> None:
    """The ambiguity reply names the days, and following its advice cancels exactly one job."""
    for scheduled in (
        "turn on the master bathroom light at 6am",
        "turn on the master bathroom light on thursday at 6am",
    ):
        assert (await say(hass, home, scheduled)).startswith("OK, ")
    thursday = manager.pending()[1]

    speech = await say(hass, home, "cancel the 6am job")
    assert speech == (
        "There are 2 jobs for master bathroom light, at 6 AM tomorrow and 6 AM on Thursday. "
        "Say 'cancel the 6 AM job tomorrow'."
    )

    speech = await say(hass, home, advice)
    assert speech.startswith("Cancelled: turn on Master Bathroom Light at 6 AM tomorrow"), speech
    assert manager.pending() == [thursday]


async def test_cancel_timer_is_left_to_assist(hass: HomeAssistant, home: Assist, manager: JobManager) -> None:
    speech = await say(hass, home, "cancel the timer")

    assert speech != "I couldn't find a scheduled job matching that."


@pytest.mark.parametrize("config_entry", [{CONF_DEFER_RELATIVE: True}], indirect=True)
async def test_defer_relative_leaves_relative_to_ha(hass: HomeAssistant, home: Assist, manager: JobManager) -> None:
    await say(hass, home, "turn on the master bathroom light in 5 minutes")
    await say(hass, home, "in 5 minutes turn on the master bathroom light")
    assert manager.pending() == []

    speech = await say(hass, home, "at 11pm turn on the master bathroom light")
    assert speech.startswith("OK, ")
    assert len(manager.pending()) == 1


async def test_plain_timer_not_captured(hass: HomeAssistant, home: Assist, manager: JobManager) -> None:
    await say(hass, home, "set a timer for 5 minutes")

    assert manager.pending() == []


async def test_unrecognized_command_refusal_speech(hass: HomeAssistant, home: Assist, manager: JobManager) -> None:
    speech = await say(hass, home, "at 10 make the living room cozy")

    assert speech == UNRECOGNIZED
    assert manager.pending() == []


async def test_unload_unregisters_triggers(
    hass: HomeAssistant, home: Assist, manager: JobManager, config_entry: MockConfigEntry
) -> None:
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    speech = await say(hass, home, "at 11pm turn on the master bathroom light")

    assert not speech.startswith("OK, ")


async def say_in(hass: HomeAssistant, home: Assist, text: str, language: str) -> str:
    result = await conversation.async_converse(hass, text, None, Context(), language, device_id=home.device_id)
    return result.response.speech["plain"]["speech"]


async def test_sentences_do_not_depend_on_the_system_language(
    hass: HomeAssistant, home: Assist, config_entry: MockConfigEntry
) -> None:
    hass.config.language = "de"
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    speech = await say(hass, home, "at 11pm turn on the master bathroom light")

    assert speech.startswith("OK, "), speech
    assert len(config_entry.runtime_data.manager.pending()) == 1


async def test_sentence_in_a_language_without_a_pack_is_left_to_assist(
    hass: HomeAssistant, home: Assist, manager: JobManager
) -> None:
    speech = await say_in(hass, home, "at 11pm turn on the master bathroom light", "de")

    assert speech == "Entschuldigung, das habe ich nicht verstanden"
    assert manager.pending() == []
    assert bathroom_light_untouched(hass, home)


async def test_each_pipeline_language_parses_with_its_own_pack(
    hass: HomeAssistant, home: Assist, config_entry: MockConfigEntry
) -> None:
    german = replace(EN, code="de", sentences={**EN.sentences, "list": ["was steht an"]})
    config_entry.add_to_hass(hass)
    with patch.dict("custom_components.at.lang._PACKS", {"de": lambda: german}):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert await say_in(hass, home, "was steht an", "de-DE") == "Nothing is scheduled."
        assert await say(hass, home, "was steht an") != "Nothing is scheduled."
        assert (await say(hass, home, "what's scheduled")) == "Nothing is scheduled."


async def test_public_fallback_when_lists_cannot_be_injected(
    hass: HomeAssistant, home: Assist, config_entry: MockConfigEntry, caplog: pytest.LogCaptureFixture
) -> None:
    config_entry.add_to_hass(hass)
    with patch("custom_components.at.ha_internal.sentence_triggers._inject_lists", return_value=False):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    manager: JobManager = config_entry.runtime_data.manager

    assert "public-only sentence triggers" in caplog.text
    assert (await say(hass, home, "turn on the master bathroom light at 6am")).startswith("OK, at 6 AM tomorrow")
    assert (await say(hass, home, "at 6:30 tonight turn on the master bathroom light")).startswith("OK, at 6:30 PM")
    await say(hass, home, "turn on the master bathroom light at home")
    assert len(manager.pending()) == 2
    # The literal fallback is looser than at's own parse; what only it accepts gets an answer, not "Done".
    assert await say(hass, home, "cancelthe bedtime script") == UNRECOGNIZED
    assert (await say(hass, home, "cancel all jobs")) == "Cancelled 2 jobs."


def test_lists_two_languages_define_differently_become_wildcards() -> None:
    async def unparsed(_given: object) -> str:
        return ""

    hour = {"range": {"from": 1, "to": 12}}
    english = LanguageSentences("en", [], {"hour": hour, "scope": {"values": ["tonight"]}}, unparsed)
    german = LanguageSentences("de", [], {"hour": hour, "scope": {"values": ["heute abend"]}}, unparsed)

    assert _gate_lists([english, german]) == {"hour": hour}


@pytest.mark.parametrize("group", ["schedule_absolute", "schedule_relative", "list", "cancel"])
def test_sentences_pass_the_trigger_schema_checks(group: str) -> None:
    sentences = EN.sentences[group]

    assert sentences
    assert has_no_punctuation(sentences) == sentences
    assert is_valid_sentence(sentences) == sentences


@pytest.mark.parametrize(
    "sentence",
    [
        pytest.param("At 11 p.m., turn on the master bathroom light.", id="absolute"),
        pytest.param("Run the bedtime script in 30 minutes.", id="relative"),
    ],
)
async def test_speech_to_text_punctuation(
    hass: HomeAssistant, home: Assist, manager: JobManager, script_calls: list[ServiceCall], sentence: str
) -> None:
    speech = await say(hass, home, sentence)

    assert speech.startswith("OK, "), speech
    assert len(manager.pending()) == 1
    assert bathroom_light_untouched(hass, home)
    assert script_calls == []


async def test_unknown_command_with_time_still_refused(hass: HomeAssistant, home: Assist, manager: JobManager) -> None:
    assert await say(hass, home, "make the living room cozy at 10") == UNRECOGNIZED
    assert manager.pending() == []


class RecordingBroadcastHandler(intent.IntentHandler):
    """Stand in for the broadcast intent and record the messages it is given."""

    intent_type = "HassBroadcast"
    slot_schema = {"message": str}

    def __init__(self) -> None:
        """Start with no messages."""
        self.messages: list[str] = []

    @override
    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Record the message and answer like the real handler."""
        self.messages.append(intent_obj.slots["message"]["value"])
        response = intent_obj.create_response()
        response.async_set_speech("Done")
        return response


@pytest.fixture
def broadcast(hass: HomeAssistant, entity_registry: er.EntityRegistry) -> RecordingBroadcastHandler:
    """Stand in for the broadcast handler, with one satellite that takes announcements."""
    entry = entity_registry.async_get_or_create(
        "assist_satellite",
        "test",
        "kitchen_satellite",
        suggested_object_id="kitchen_satellite",
        supported_features=AssistSatelliteEntityFeature.ANNOUNCE,
    )
    hass.states.async_set(entry.entity_id, "idle")
    handler = RecordingBroadcastHandler()
    intent.async_register(hass, handler)
    return handler


async def test_full_sentence_handed_to_assist_intent(
    hass: HomeAssistant, home: Assist, manager: JobManager, broadcast: RecordingBroadcastHandler
) -> None:
    """A time after the message is part of it: the whole sentence goes back and HA broadcasts "dinner is at 6"."""
    speech = await say(hass, home, "broadcast dinner is at 6")

    assert speech != UNRECOGNIZED
    assert manager.pending() == []
    assert broadcast.messages == ["dinner is at 6"]


async def test_broadcast_with_its_time_first_is_scheduled(
    hass: HomeAssistant, home: Assist, manager: JobManager, broadcast: RecordingBroadcastHandler
) -> None:
    speech = await say(hass, home, "at 6pm broadcast dinner is ready")

    assert speech == 'OK, at 6 PM tomorrow I\'ll broadcast "dinner is ready".'
    assert [job.intent.type for job in manager.pending() if job.intent] == ["HassBroadcast"]
    assert broadcast.messages == []


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


@pytest.fixture
async def llm_pipeline(hass: HomeAssistant, manager: JobManager) -> StubLlmAgent:
    """Make a stub LLM the pipeline's agent, with prefer-local on."""
    stub_agent = StubLlmAgent()
    await use_agent(hass, stub_agent)
    return stub_agent


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


async def test_unknown_command_goes_to_llm_agent_once(
    hass: HomeAssistant, home: Assist, manager: JobManager, llm_pipeline: StubLlmAgent
) -> None:
    speech = await run_pipeline(hass, home, "remind me at 5")

    assert speech == "stub agent"
    assert llm_pipeline.texts == ["remind me at 5"]
    assert manager.pending() == []


async def test_known_command_scheduled_without_llm(
    hass: HomeAssistant, home: Assist, manager: JobManager, llm_pipeline: StubLlmAgent
) -> None:
    speech = await run_pipeline(hass, home, "at 11pm turn on the master bathroom light")

    assert speech.startswith("OK, at 11 PM")
    assert llm_pipeline.texts == []
    assert len(manager.pending()) == 1


LONG_REPLY = "I can't set reminders, but I can schedule a light or a script for later if you like."


class StreamingStubAgent(conversation.AbstractConversationAgent):
    """A stand-in LLM that answers through its chat log by streaming, like the real ones."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Start with no calls."""
        self.hass = hass
        self.seen: list[list[conversation.Content]] = []

    @property
    @override
    def supported_languages(self) -> list[str] | str:
        """Accept every language."""
        return MATCH_ALL

    @override
    async def async_process(self, user_input: conversation.ConversationInput) -> conversation.ConversationResult:
        """Record the history it was given, then stream a long reply into it."""
        with (
            chat_session.async_get_chat_session(self.hass, user_input.conversation_id) as session,
            conversation.async_get_chat_log(self.hass, session, user_input) as chat_log,
        ):
            self.seen.append(list(chat_log.content))

            async def stream() -> AsyncIterator[conversation.AssistantContentDeltaDict]:
                yield {"role": "assistant"}
                yield {"content": LONG_REPLY[:30]}
                yield {"content": LONG_REPLY[30:]}

            async for _content in chat_log.async_add_delta_content_stream("stub", stream()):
                pass
            response = intent.IntentResponse(language=user_input.language)
            response.async_set_speech(LONG_REPLY)
            return conversation.ConversationResult(response=response, conversation_id=chat_log.conversation_id)


async def use_agent(hass: HomeAssistant, agent: conversation.AbstractConversationAgent) -> str:
    """Make ``agent`` the pipeline's agent, with prefer-local on, and return its agent id."""
    assert await async_setup_component(hass, "assist_pipeline", {})
    agent_entry = MockConfigEntry(domain="test", title="Stub LLM")
    agent_entry.add_to_hass(hass)
    conversation.async_set_agent(hass, agent_entry, agent)
    (pipeline,) = async_get_pipelines(hass)
    await async_update_pipeline(hass, pipeline, conversation_engine=agent_entry.entry_id, prefer_local_intents=True)
    return agent_entry.entry_id


@pytest.mark.parametrize(
    "chat_log_variable",
    [pytest.param(current_chat_log, id="chat-log-cleared"), pytest.param(None, id="private-chat-log-variable-missing")],
)
async def test_llm_hand_off_uses_its_own_chat_log(
    hass: HomeAssistant, home: Assist, manager: JobManager, chat_log_variable: object
) -> None:
    stub_agent = StreamingStubAgent(hass)
    await use_agent(hass, stub_agent)

    with patch("custom_components.at.ha_internal.fallthrough.current_chat_log", chat_log_variable):
        async with asyncio.timeout(10):
            speech, conversation_id = await run_pipeline_with_id(hass, home, "remind me at 5")

    assert speech == LONG_REPLY
    assert manager.pending() == []
    (history,) = stub_agent.seen
    assert [(c.role, c.content) for c in history if c.role != "system"] == [("user", "remind me at 5")]
    with (
        chat_session.async_get_chat_session(hass, conversation_id) as session,
        conversation.async_get_chat_log(hass, session) as chat_log,
    ):
        pipeline_log = [c for c in chat_log.content if c.role != "system"]
    assert [c.role for c in pipeline_log] == ["user", "assistant", "tool_result", "assistant"]
    assert [tool.tool_name for tool in pipeline_log[1].tool_calls or []] == ["trigger_sentence"]
    assert pipeline_log[-1].content == LONG_REPLY


class FailingAgent(StubLlmAgent):
    """A non-default agent that breaks."""

    @override
    async def async_process(self, user_input: conversation.ConversationInput) -> conversation.ConversationResult:
        """Fail every sentence."""
        self.texts.append(user_input.text)
        msg = "agent exploded"
        raise RuntimeError(msg)


async def test_failing_agent_gets_refusal_not_crash(
    hass: HomeAssistant, home: Assist, manager: JobManager, caplog: pytest.LogCaptureFixture
) -> None:
    failing_agent = FailingAgent()
    await use_agent(hass, failing_agent)

    speech = await run_pipeline(hass, home, "remind me at 5")

    assert speech == UNRECOGNIZED
    assert failing_agent.texts == ["remind me at 5"]
    assert manager.pending() == []
    assert "agent exploded" in caplog.text


class BlockingStubAgent(StubLlmAgent):
    """A stand-in LLM that never answers, and notes when it is cancelled."""

    def __init__(self) -> None:
        """Start waiting for nothing."""
        super().__init__()
        self.entered = asyncio.Event()
        self.cancelled = False

    @override
    async def async_process(self, user_input: conversation.ConversationInput) -> conversation.ConversationResult:
        """Block until cancelled."""
        self.texts.append(user_input.text)
        self.entered.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancelled = True
            raise
        raise AssertionError


async def test_cancelled_trigger_cancels_the_hand_off(hass: HomeAssistant, manager: JobManager) -> None:
    """The hand-off runs as its own task, so cancelling the trigger callback must cancel the forwarded call too."""
    agent = BlockingStubAgent()
    agent_id = await use_agent(hass, agent)
    given = TriggerInput("remind me at 5", {}, "en", None, None, Context(), agent_id=agent_id)

    hand_off = hass.async_create_task(async_hand_off(hass, given))
    async with asyncio.timeout(5):
        await agent.entered.wait()
    hand_off.cancel()
    with pytest.raises(asyncio.CancelledError):
        await hand_off

    assert agent.cancelled
    assert agent.texts == ["remind me at 5"]
