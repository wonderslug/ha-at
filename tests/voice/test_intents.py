"""The AtSchedule, AtList and AtCancel intent handlers."""

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.at.core.manager import JobManager
from custom_components.at.core.models import Job, JobKind, JobStatus, Result, Source, Targets, Via, new_job_id
from custom_components.at.voice.intents import INTENT_CANCEL, INTENT_LIST, INTENT_SCHEDULE, AtListHandler
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import entity_registry as er, intent
from homeassistant.util import dt as dt_util
from tests.assist import ASSISTANT, Assist  # noqa: TID251  (plain module; see tests/assist.py)

pytestmark = [
    pytest.mark.real_dependencies,
    pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning"),
]

UNSUPPORTED = "Sorry, scheduling is only available in English for now."


@pytest.fixture
async def manager(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    assist: Assist,
    entity_registry: er.EntityRegistry,
    config_entry: MockConfigEntry,
) -> JobManager:
    """Freeze now at 22:22 Chicago, expose a porch light, and load the integration."""
    await hass.config.async_set_time_zone("America/Chicago")
    freezer.move_to("2026-11-18 04:22:00+00:00")
    entry = entity_registry.async_get_or_create(
        "light", "test", "porch", suggested_object_id="porch", original_name="Porch Light"
    )
    hass.states.async_set(entry.entity_id, "off", {ATTR_FRIENDLY_NAME: "Porch Light"})
    async_expose_entity(hass, ASSISTANT, entry.entity_id, True)
    async_mock_service(hass, "light", "turn_on")
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry.runtime_data.manager


async def handle(hass: HomeAssistant, intent_type: str, slots: dict, language: str = "en"):
    return await intent.async_handle(
        hass, "test", intent_type, {k: {"value": v} for k, v in slots.items()}, language=language
    )


def speech(response) -> str:
    return response.speech["plain"]["speech"]


async def add_job(manager: JobManager, summary: str, hours: int, via: Via = Via.VOICE, names=()) -> Job:
    return await manager.async_add(
        Job(
            id=new_job_id(),
            kind=JobKind.INTENT,
            status=JobStatus.PENDING,
            due=dt_util.utcnow() + timedelta(hours=hours),
            created_at=dt_util.utcnow(),
            finished_at=None,
            summary=summary,
            original_text=summary,
            intent=None,
            action=None,
            raw_action=False,
            targets=Targets(names=list(names)),
            source=Source(via=via, user_id=None, device_id=None, agent_id=None),
            result=Result(),
        )
    )


async def test_at_schedule_intent_creates_job(hass: HomeAssistant, manager: JobManager) -> None:
    response = await handle(hass, INTENT_SCHEDULE, {"time": "at 11pm", "command": "turn on the porch light"})

    assert speech(response) == "OK, at 11 PM I'll turn on Porch Light."
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert len(manager.pending()) == 1
    assert manager.pending()[0].source.via == Via.VOICE


async def test_at_schedule_intent_refusal_is_error_response(hass: HomeAssistant, manager: JobManager) -> None:
    response = await handle(hass, INTENT_SCHEDULE, {"time": "at 11pm", "command": "dance wildly"})

    assert response.response_type == intent.IntentResponseType.ERROR
    assert "I can only schedule commands I can check" in speech(response)
    assert manager.pending() == []


async def test_bad_time_is_error_response(hass: HomeAssistant, manager: JobManager) -> None:
    response = await handle(hass, INTENT_SCHEDULE, {"time": "whenever", "command": "turn on the porch light"})

    assert response.response_type == intent.IntentResponseType.ERROR
    assert speech(response) == "Sorry, I didn't understand when."


async def test_unsupported_language_refuses(hass: HomeAssistant, manager: JobManager) -> None:
    for intent_type, slots in (
        (INTENT_SCHEDULE, {"time": "at 11pm", "command": "turn on the porch light"}),
        (INTENT_LIST, {}),
        (INTENT_CANCEL, {"all": True}),
    ):
        response = await handle(hass, intent_type, slots, language="de")
        assert response.response_type == intent.IntentResponseType.ERROR
        assert speech(response) == UNSUPPORTED
    assert manager.pending() == []


async def test_at_list_intent_speech(hass: HomeAssistant, manager: JobManager) -> None:
    assert speech(await handle(hass, INTENT_LIST, {})) == "Nothing is scheduled."
    await add_job(manager, "Turn on Porch Light", 1)
    await add_job(manager, "Turn off Porch Light", 20)

    response = await handle(hass, INTENT_LIST, {})
    assert speech(response).startswith("2 scheduled: turn on Porch Light at 11:22 PM")
    today = await handle(hass, INTENT_LIST, {"scope": "tomorrow"})
    assert speech(today).startswith("1 scheduled: turn off Porch Light")
    named = await handle(hass, INTENT_LIST, {"name": "nothing like this"})
    assert speech(named) == "Nothing is scheduled."


async def test_at_cancel_intent_all_skips_service(hass: HomeAssistant, manager: JobManager) -> None:
    await add_job(manager, "Turn on Porch Light", 1)
    await add_job(manager, "Turn on Porch Light", 2, via=Via.LLM)
    kept = await add_job(manager, "Turn on Porch Light", 3, via=Via.SERVICE)

    response = await intent.async_handle(
        hass, "test", INTENT_CANCEL, {"all": {"value": True}}, language="en", context=Context(user_id="voice-user")
    )

    assert speech(response) == "Cancelled 2 jobs. 1 job created by automations was left alone."
    assert manager.history()[0].result.cancelled_user_id == "voice-user"
    assert [j.id for j in manager.pending()] == [kept.id]
    assert manager.history()[0].result.cancelled_by == "voice"


async def test_at_cancel_all_records_satellite(hass: HomeAssistant, manager: JobManager) -> None:
    await add_job(manager, "Turn on Porch Light", 1)
    await intent.async_handle(hass, "test", INTENT_CANCEL, {"all": {"value": True}}, language="en", device_id="sat-1")
    assert manager.history()[0].result.cancelled_device_id == "sat-1"


async def test_at_cancel_one_records_satellite(hass: HomeAssistant, manager: JobManager) -> None:
    await add_job(manager, "Turn on Porch Light", 1, names=["Porch Light"])
    await intent.async_handle(
        hass, "test", INTENT_CANCEL, {"name": {"value": "porch"}}, language="en", device_id="sat-1"
    )
    assert manager.history()[0].result.cancelled_device_id == "sat-1"


async def test_at_cancel_by_name_and_time(hass: HomeAssistant, manager: JobManager) -> None:
    await add_job(manager, "Turn on Porch Light", 1, names=["Porch Light"])
    await add_job(manager, "Turn on Hall Light", 2, names=["Hall Light"])

    none = await handle(hass, INTENT_CANCEL, {"name": "garage"})
    assert speech(none) == "I couldn't find a scheduled job matching that."

    one = await handle(hass, INTENT_CANCEL, {"name": "porch"})
    assert speech(one).startswith("Cancelled: turn on Porch Light")
    assert len(manager.pending()) == 1

    by_time = await handle(hass, INTENT_CANCEL, {"time": "at 12:22am"})
    assert speech(by_time).startswith("Cancelled: turn on Hall Light")
    assert manager.pending() == []


async def test_at_cancel_by_relative_time(hass: HomeAssistant, manager: JobManager) -> None:
    await add_job(manager, "Turn on Porch Light", 2, names=["Porch Light"])
    await add_job(manager, "Turn on Hall Light", 5, names=["Hall Light"])

    response = await handle(hass, INTENT_CANCEL, {"time": "in 2 hours"})

    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert speech(response).startswith("Cancelled: turn on Porch Light")
    assert [j.summary for j in manager.pending()] == ["Turn on Hall Light"]


async def test_at_cancel_ambiguous_cancels_nothing(hass: HomeAssistant, manager: JobManager) -> None:
    await add_job(manager, "Turn on Porch Light", 1, names=["Porch Light"])
    await add_job(manager, "Turn off Porch Light", 2, names=["Porch Light"])

    response = await handle(hass, INTENT_CANCEL, {"name": "porch"})

    assert speech(response).startswith("There are 2 jobs for Porch Light")
    assert len(manager.pending()) == 2


async def test_at_cancel_without_criteria_cancels_nothing(hass: HomeAssistant, manager: JobManager) -> None:
    await add_job(manager, "Turn on Porch Light", 1)

    response = await handle(hass, INTENT_CANCEL, {})

    assert speech(response) == "I couldn't find a scheduled job matching that."
    assert len(manager.pending()) == 1


async def test_unload_removes_handlers_and_reload_restores_them(
    hass: HomeAssistant, manager: JobManager, config_entry: MockConfigEntry
) -> None:
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    with pytest.raises(intent.UnknownIntent):
        await handle(hass, INTENT_LIST, {})

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    response = await handle(hass, INTENT_SCHEDULE, {"time": "at 11pm", "command": "turn on the porch light"})
    assert speech(response) == "OK, at 11 PM I'll turn on Porch Light."
    assert len(config_entry.runtime_data.manager.pending()) == 1


async def test_handler_without_loaded_entry_is_error(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    obj = intent.Intent(hass, "test", INTENT_LIST, {}, None, Context(), "en")

    response = await AtListHandler().async_handle(obj)

    assert response.response_type == intent.IntentResponseType.ERROR
    assert speech(response) == "Sorry, scheduling isn't set up."
