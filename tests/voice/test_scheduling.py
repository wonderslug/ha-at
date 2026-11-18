"""The shared schedule-from-text pipeline."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.at.core.models import JobKind, JobStatus, Via
from custom_components.at.voice.scheduling import ScheduleRefused, async_schedule_command
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from tests.assist import ASSISTANT, LANGUAGE, Assist  # noqa: TID251  (plain module; see tests/assist.py)

CHICAGO = ZoneInfo("America/Chicago")
UNRECOGNIZED = (
    "Sorry, I can only schedule commands I can check right now. Try rephrasing, or schedule a script or scene."
)

pytestmark = [
    pytest.mark.real_dependencies,
    pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning"),
]


@pytest.fixture
async def home(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, assist: Assist, entity_registry: er.EntityRegistry
) -> Assist:
    """Freeze now at 22:22 Chicago on 2026-11-17 and add two named lights."""
    await hass.config.async_set_time_zone("America/Chicago")
    freezer.move_to("2026-11-18 04:22:00+00:00")
    for object_id, name in (("master_bathroom", "Master Bathroom Light"), ("porch", "Porch Light")):
        entry = entity_registry.async_get_or_create(
            "light", "test", object_id, suggested_object_id=object_id, original_name=name
        )
        hass.states.async_set(entry.entity_id, "off", {ATTR_FRIENDLY_NAME: name})
        async_expose_entity(hass, ASSISTANT, entry.entity_id, True)
    async_mock_service(hass, "light", "turn_on")
    await hass.async_block_till_done()
    return assist


@pytest.fixture
def manager() -> MagicMock:
    mock = MagicMock()
    mock.async_add = AsyncMock(side_effect=lambda job: job)
    return mock


async def schedule(hass: HomeAssistant, manager: MagicMock, home: Assist, command: str, time_text: str | None, **kw):
    return await async_schedule_command(
        hass,
        manager,
        command_text=command,
        time_text=time_text,
        language=kw.pop("language", LANGUAGE),
        via=Via.VOICE,
        user_id="user1",
        device_id=home.device_id,
        satellite_id=None,
        **kw,
    )


async def test_schedules_absolute_and_confirms(hass: HomeAssistant, manager: MagicMock, home: Assist) -> None:
    outcome = await schedule(hass, manager, home, "turn on the master bathroom light", "at 6am")

    assert outcome.speech == "OK, at 6 AM tomorrow I'll turn on Master Bathroom Light."
    job = outcome.job
    assert job.kind == JobKind.INTENT
    assert job.status == JobStatus.PENDING
    assert job.due.astimezone(CHICAGO).isoformat() == "2026-11-18T06:00:00-06:00"
    assert job.source.via == Via.VOICE
    assert job.source.user_id == "user1"
    assert job.source.device_id == home.device_id
    assert job.original_text == "turn on the master bathroom light"
    manager.async_add.assert_awaited_once_with(job)


async def test_schedules_relative_and_confirms(hass: HomeAssistant, manager: MagicMock, home: Assist) -> None:
    outcome = await schedule(hass, manager, home, "turn on the master bathroom light", "in 20 minutes")

    assert outcome.speech == "OK, in 20 minutes, at 10:42 PM, I'll turn on Master Bathroom Light."


async def test_time_split_from_command_text(hass: HomeAssistant, manager: MagicMock, home: Assist) -> None:
    outcome = await schedule(hass, manager, home, "turn on the porch light at 11pm", None)

    assert outcome.job.due.astimezone(CHICAGO).hour == 23
    assert outcome.speech == "OK, at 11 PM I'll turn on Porch Light."
    assert outcome.job.original_text == "turn on the porch light at 11pm"


async def test_day_qualifiers(hass: HomeAssistant, manager: MagicMock, home: Assist) -> None:
    friday = await schedule(hass, manager, home, "turn on the porch light", "on friday at 8am")
    assert friday.speech == "OK, at 8 AM on Friday I'll turn on Porch Light."
    due = friday.job.due.astimezone(CHICAGO)
    assert due.isoformat() == "2026-11-20T08:00:00-06:00"

    later = await schedule(
        hass,
        manager,
        home,
        "turn on the porch light",
        None,
        due=due.replace(month=12, day=3, hour=0, minute=0),
    )
    assert later.speech == "OK, at 12 AM on December 3 I'll turn on Porch Light."


async def test_due_given_skips_time_parsing(hass: HomeAssistant, manager: MagicMock, home: Assist) -> None:
    due = datetime(2026, 11, 18, 6, 30, tzinfo=CHICAGO)
    outcome = await schedule(hass, manager, home, "turn on the porch light", "at noon", due=due)

    assert outcome.job.due == due
    assert outcome.speech == "OK, at 6:30 AM tomorrow I'll turn on Porch Light."


async def test_refuses_unrecognized(hass: HomeAssistant, manager: MagicMock, home: Assist) -> None:
    with pytest.raises(ScheduleRefused) as exc:
        await schedule(hass, manager, home, "make the living room cozy", "at 6am")

    assert exc.value.speech == UNRECOGNIZED
    manager.async_add.assert_not_called()


async def test_refuses_bad_time(hass: HomeAssistant, manager: MagicMock, home: Assist) -> None:
    with pytest.raises(ScheduleRefused) as exc:
        await schedule(hass, manager, home, "turn on the porch light", "whenever")

    assert exc.value.speech == "Sorry, I didn't understand when."
    manager.async_add.assert_not_called()


async def test_dry_run_does_not_add(hass: HomeAssistant, manager: MagicMock, home: Assist) -> None:
    outcome = await schedule(hass, manager, home, "turn on the porch light", "at 6am", dry_run=True)

    assert outcome.job.id
    assert outcome.job.intent is not None
    assert outcome.job.targets.entity_ids == ["light.porch"]
    assert outcome.speech == "OK, at 6 AM tomorrow I'll turn on Porch Light."
    manager.async_add.assert_not_called()


async def test_unsupported_language_refuses(hass: HomeAssistant, manager: MagicMock, home: Assist) -> None:
    with (
        patch("custom_components.at.voice.scheduling.parse_time_text") as parse,
        patch("custom_components.at.voice.scheduling.split_time_and_command") as split,
        patch("custom_components.at.voice.scheduling.async_recognize_command") as recognize,
        pytest.raises(ScheduleRefused) as exc,
    ):
        await schedule(hass, manager, home, "schalte das Licht ein", "um 6 Uhr", language="de")

    assert exc.value.speech == "Sorry, scheduling is only available in English for now."
    parse.assert_not_called()
    split.assert_not_called()
    recognize.assert_not_called()
