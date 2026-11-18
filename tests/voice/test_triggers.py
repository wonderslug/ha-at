"""Sentence triggers on the built-in agent: schedule, list and cancel by voice."""

import logging
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.at.const import CONF_DEFER_RELATIVE
from custom_components.at.core.manager import JobManager
from custom_components.at.lang.en import EN
from homeassistant.components import conversation
from homeassistant.components.conversation.trigger import has_no_punctuation, is_valid_sentence
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from tests.assist import ASSISTANT, LANGUAGE, Assist  # noqa: TID251  (plain module; see tests/assist.py)

pytestmark = [
    pytest.mark.real_dependencies,
    pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning"),
]

UNRECOGNIZED = (
    "Sorry, I can only schedule commands I can check right now. Try rephrasing, or schedule a script or scene."
)
LIGHT = "light.master_bathroom"


@pytest.fixture
async def home(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, assist: Assist, entity_registry: er.EntityRegistry
) -> Assist:
    """Freeze now at 22:22 Chicago on Tuesday 2026-11-17 and expose the bathroom light and the bedtime script."""
    await hass.config.async_set_time_zone("America/Chicago")
    freezer.move_to("2026-11-18 04:22:00+00:00")
    for domain, object_id, name in (
        ("light", "master_bathroom", "Master Bathroom Light"),
        ("script", "bedtime", "Bedtime"),
    ):
        entry = entity_registry.async_get_or_create(
            domain, "test", object_id, suggested_object_id=object_id, original_name=name
        )
        hass.states.async_set(entry.entity_id, "off", {ATTR_FRIENDLY_NAME: name})
        async_expose_entity(hass, ASSISTANT, entry.entity_id, True)
    await hass.async_block_till_done()
    return assist


@pytest.fixture
def script_calls(hass: HomeAssistant) -> list[ServiceCall]:
    """Record script runs instead of running them."""
    return async_mock_service(hass, "script", "turn_on")


@pytest.fixture
async def manager(hass: HomeAssistant, home: Assist, config_entry: MockConfigEntry) -> JobManager:
    """Load the integration once the home is set up."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry.runtime_data.manager


async def say(hass: HomeAssistant, home: Assist, text: str) -> str:
    result = await conversation.async_converse(hass, text, None, Context(), LANGUAGE, device_id=home.device_id)
    return result.response.speech["plain"]["speech"]


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
    ],
)
async def test_time_and_command_are_split_cleanly(
    hass: HomeAssistant, home: Assist, manager: JobManager, sentence: str, expected: str
) -> None:
    speech = await say(hass, home, sentence)

    assert speech.startswith(expected), speech
    assert speech.endswith(("Master Bathroom Light.", "Bedtime.")), speech


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


async def test_unsupported_language_registers_nothing(
    hass: HomeAssistant, home: Assist, config_entry: MockConfigEntry, caplog: pytest.LogCaptureFixture
) -> None:
    hass.config.language = "de"
    config_entry.add_to_hass(hass)
    with caplog.at_level(logging.INFO):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    hass.config.language = "en"

    speech = await say(hass, home, "at 11pm turn on the master bathroom light")

    assert not speech.startswith("OK, ")
    assert config_entry.runtime_data.manager.pending() == []
    assert "no voice sentences for language de" in caplog.text


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
    assert (await say(hass, home, "cancel all jobs")) == "Cancelled 2 jobs."


@pytest.mark.parametrize("group", ["schedule_absolute", "schedule_relative", "list", "cancel"])
def test_sentences_pass_the_trigger_schema_checks(group: str) -> None:
    sentences = EN.sentences[group]

    assert sentences
    assert has_no_punctuation(sentences) == sentences
    assert is_valid_sentence(sentences) == sentences
