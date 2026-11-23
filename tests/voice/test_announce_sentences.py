"""Announcement sentences: no message, the place after the message, and refusals handed back to an LLM agent."""

from dataclasses import dataclass
from typing import override

import pytest
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.at.core.manager import JobManager
from homeassistant.components import conversation
from homeassistant.components.assist_satellite.const import AssistSatelliteEntityFeature
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import area_registry as ar, entity_registry as er, floor_registry as fr
from tests.assist import (  # noqa: TID251  (plain module; see tests/assist.py)
    STUB_SPEECH,
    Assist,
    StubLlmAgent,
    run_pipeline,
    say,
    use_agent,
)
from tests.voice.conftest import RecordingBroadcastHandler  # noqa: TID251  (fixture types)

pytestmark = [
    pytest.mark.real_dependencies,
    pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning"),
]

SUITE_SPEAKER = "assist_satellite.suite_room_speaker"
KITCHEN_SPEAKER = "assist_satellite.kitchen_speaker"
LAMP = "light.suite_room_table_lamp"


@dataclass
class Places:
    """The rooms an announcement can go to, and what reached them."""

    announcements: list[ServiceCall]
    lamp_off_calls: list[ServiceCall]

    def heard(self) -> list[tuple[list[str], str]]:
        return [(call.data["entity_id"], call.data["message"]) for call in self.announcements]


@pytest.fixture
async def places(
    hass: HomeAssistant,
    home: Assist,
    area_registry: ar.AreaRegistry,
    floor_registry: fr.FloorRegistry,
    entity_registry: er.EntityRegistry,
) -> Places:
    """
    Add Upstairs with the Suite Room, the Ground Floor with the Kitchen, and a Garage with no speaker.

    The Suite Room and the Kitchen each have an announcing speaker; the Suite Room has an exposed table lamp.
    """
    upstairs = floor_registry.async_create("Upstairs")
    ground = floor_registry.async_create("Ground Floor")
    suite = area_registry.async_create("Suite Room", floor_id=upstairs.floor_id)
    kitchen = area_registry.async_create("Kitchen", floor_id=ground.floor_id)
    area_registry.async_create("Garage")
    for object_id, area in (("suite_room_speaker", suite), ("kitchen_speaker", kitchen)):
        entry = entity_registry.async_get_or_create(
            "assist_satellite",
            "test",
            object_id,
            suggested_object_id=object_id,
            supported_features=AssistSatelliteEntityFeature.ANNOUNCE,
        )
        entity_registry.async_update_entity(entry.entity_id, area_id=area.id)
        hass.states.async_set(entry.entity_id, "idle")
    lamp = entity_registry.async_get_or_create(
        "light", "test", "suite_lamp", suggested_object_id="suite_room_table_lamp", original_name="Table Lamp"
    )
    entity_registry.async_update_entity(lamp.entity_id, area_id=suite.id)
    hass.states.async_set(lamp.entity_id, "on", {ATTR_FRIENDLY_NAME: "Suite Room Table Lamp"})
    async_expose_entity(hass, "conversation", lamp.entity_id, True)
    await hass.async_block_till_done()
    return Places(
        announcements=async_mock_service(hass, "assist_satellite", "announce"),
        lamp_off_calls=async_mock_service(hass, "light", "turn_off"),
    )


def place_jobs(manager: JobManager) -> list[tuple[str, dict[str, object]]]:
    return [
        (
            job.intent.type,
            {name: slot["value"] for name, slot in job.intent.slots.items() if name != "preferred_area_id"},
        )
        for job in manager.pending()
        if job.intent is not None
    ]


@pytest.mark.parametrize(
    ("sentence", "expected"),
    [
        pytest.param(
            "In one minute, announce in the suite room",
            "What should I announce in the Suite Room?",
            id="reported-cut-off-relative",
        ),
        pytest.param("announce in the kitchen", "What should I announce in the Kitchen?", id="area-now"),
        pytest.param("broadcast to upstairs", "What should I announce on Upstairs?", id="floor-now"),
        pytest.param("tell everyone in the kitchen", "What should I announce in the Kitchen?", id="tell-area"),
        pytest.param("at 11pm announce in the kitchen", "What should I announce in the Kitchen?", id="area-later"),
        pytest.param("in 5 minutes broadcast to upstairs", "What should I announce on Upstairs?", id="floor-later"),
        pytest.param("announce upstairs", "What should I announce on Upstairs?", id="bare-floor"),
    ],
)
async def test_announcement_without_a_message_is_refused(
    hass: HomeAssistant,
    home: Assist,
    manager: JobManager,
    places: Places,
    broadcast: RecordingBroadcastHandler,
    sentence: str,
    expected: str,
) -> None:
    speech = await say(hass, home, sentence)

    assert speech == expected
    assert manager.pending() == []
    assert places.announcements == []
    assert broadcast.messages == []


async def test_announcement_without_a_message_is_not_handed_to_an_llm(
    hass: HomeAssistant, home: Assist, manager: JobManager, places: Places, llm_pipeline: StubLlmAgent
) -> None:
    speech = await run_pipeline(hass, home, "In one minute, announce in the suite room")

    assert speech == "What should I announce in the Suite Room?"
    assert llm_pipeline.texts == []
    assert manager.pending() == []


@pytest.mark.usefixtures("manager")
@pytest.mark.parametrize(
    ("sentence", "speaker", "message"),
    [
        pytest.param("Announce that its Bed Time in the Suite Room", SUITE_SPEAKER, "its Bed Time", id="reported"),
        pytest.param("announce the pizza is here in the kitchen", KITCHEN_SPEAKER, "the pizza is here", id="area"),
        pytest.param(
            "broadcast thats dinner to the kitchen",  # codespell:ignore thats
            KITCHEN_SPEAKER,
            "dinner",
            id="misheard-that-s",
        ),
        pytest.param(
            "tell everyone that dinner is ready in the kitchen", KITCHEN_SPEAKER, "dinner is ready", id="tell"
        ),
        pytest.param("tell everybody bedtime on upstairs", SUITE_SPEAKER, "bedtime", id="tell-floor"),
        pytest.param(
            "announce dinner is ready on the ground floor", KITCHEN_SPEAKER, "dinner is ready", id="floor-with-the"
        ),
        pytest.param(
            "tell everyone the cat is in the kitchen", KITCHEN_SPEAKER, "the cat is", id="message-ends-in-area"
        ),
    ],
)
async def test_place_after_the_message_now(
    hass: HomeAssistant, home: Assist, places: Places, sentence: str, speaker: str, message: str
) -> None:
    assert await say(hass, home, sentence) == "Done"
    assert places.heard() == [([speaker], message)]


@pytest.mark.parametrize(
    ("sentence", "slots"),
    [
        pytest.param(
            "in 5 minutes announce the pizza is here in the kitchen",
            {"area": "kitchen", "message": "the pizza is here"},
            id="place-last",
        ),
        pytest.param(
            "in 1 minute announce in the Suite Room the pizza is here",
            {"area": "suite_room", "message": "the pizza is here"},
            id="place-first",
        ),
        pytest.param(
            "at 11pm announce in the kitchen thats bedtime",  # codespell:ignore thats
            {"area": "kitchen", "message": "bedtime"},
            id="misheard-that-s",
        ),
        pytest.param(
            "at 11pm broadcast dinner is ready on the ground floor",
            {"floor": "ground_floor", "message": "dinner is ready"},
            id="floor-last",
        ),
    ],
)
async def test_place_announcement_scheduled(
    hass: HomeAssistant, home: Assist, manager: JobManager, places: Places, sentence: str, slots: dict[str, str]
) -> None:
    speech = await say(hass, home, sentence)

    assert speech.startswith("OK, "), speech
    assert place_jobs(manager) == [("PlaceAnnounce", slots)]
    assert places.announcements == []


@pytest.mark.usefixtures("manager", "places")
@pytest.mark.parametrize(
    ("sentence", "message"),
    [
        pytest.param("tell everyone that dinner is ready", "dinner is ready", id="tell-everyone"),
        pytest.param("let everybody know dinner is in the oven", "dinner is in the oven", id="no-such-area"),
        pytest.param("tell everyone dinner is ready upstairs", "dinner is ready upstairs", id="floor-without-on"),
    ],
)
async def test_whole_house_announcements_are_unchanged(
    hass: HomeAssistant, home: Assist, broadcast: RecordingBroadcastHandler, sentence: str, message: str
) -> None:
    assert await say(hass, home, sentence) == "Done"
    assert broadcast.messages == [message]


@pytest.mark.usefixtures("manager")
async def test_command_after_and_stays_in_the_message(hass: HomeAssistant, home: Assist, places: Places) -> None:
    """
    Document reported case 4: everything after the place is the message, a command after "and" included.

    A message may itself contain "and", so splitting on it would cut real messages in two.
    """
    speech = await say(
        hass,
        home,
        'Announce in the Suite Room thats "Its Bed Time" and turn off the suite room table lamp',  # codespell:ignore thats
    )

    assert speech == "Done"
    assert places.heard() == [([SUITE_SPEAKER], '"Its Bed Time" and turn off the suite room table lamp')]
    assert places.lamp_off_calls == []


NO_TARGET_SENTENCES = [
    pytest.param(
        "in 15 seconds turn off the Suite Room Table Lamp and Announce that Bed Time in the Suite Room",
        id="reported-two-commands",
    ),
    pytest.param("In 30 seconds it's announced in the suite room that pizza is ready", id="reported-misheard"),
    pytest.param("announce in the garage that the car is here", id="announce-no-speaker"),
    pytest.param("at 11pm announce in the garage that the car is here", id="schedule-no-speaker"),
    pytest.param("run the attic fan in 10 minutes", id="run-unknown"),
]


@pytest.mark.usefixtures("places")
@pytest.mark.parametrize("sentence", NO_TARGET_SENTENCES)
async def test_no_target_goes_to_the_llm_agent(
    hass: HomeAssistant, home: Assist, manager: JobManager, llm_pipeline: StubLlmAgent, sentence: str
) -> None:
    speech = await run_pipeline(hass, home, sentence)

    assert speech == STUB_SPEECH
    assert llm_pipeline.texts == [sentence]
    assert manager.pending() == []


@pytest.mark.usefixtures("places")
@pytest.mark.parametrize("sentence", NO_TARGET_SENTENCES)
async def test_no_target_is_refused_on_the_built_in_agent(
    hass: HomeAssistant, home: Assist, manager: JobManager, sentence: str
) -> None:
    speech = await say(hass, home, sentence)

    assert speech.startswith(("Sorry, I am not aware of", "I couldn't find")), speech
    assert manager.pending() == []


class FailingLlmAgent(StubLlmAgent):
    """A non-default agent that breaks on every sentence."""

    @override
    async def async_process(self, user_input: conversation.ConversationInput) -> conversation.ConversationResult:
        """Fail every sentence."""
        self.texts.append(user_input.text)
        msg = "agent exploded"
        raise RuntimeError(msg)


@pytest.mark.usefixtures("places")
async def test_no_target_refusal_spoken_when_the_llm_fails(
    hass: HomeAssistant, home: Assist, manager: JobManager, caplog: pytest.LogCaptureFixture
) -> None:
    agent = FailingLlmAgent()
    await use_agent(hass, agent)
    sentence = "in 15 seconds turn off the Suite Room Table Lamp and Announce that Bed Time in the Suite Room"

    speech = await run_pipeline(hass, home, sentence)

    assert speech.startswith("Sorry, I am not aware of"), speech
    assert agent.texts == [sentence]
    assert manager.pending() == []
    assert "agent exploded" in caplog.text
