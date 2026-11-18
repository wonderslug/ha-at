"""Running an automation by voice: now through a sentence, and later through a stored job."""

import pytest
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.at.core.manager import JobManager
from custom_components.at.core.models import JobKind
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from tests.assist import ASSISTANT, Assist, say  # noqa: TID251  (plain module; see tests/assist.py)

pytestmark = [
    pytest.mark.real_dependencies,
    pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning"),
]

AUTOMATION = "automation.log_bed_light"


@pytest.fixture
def trigger_calls(hass: HomeAssistant, home: Assist, entity_registry: er.EntityRegistry) -> list[ServiceCall]:
    """Expose an automation and record its triggers instead of running it."""
    entry = entity_registry.async_get_or_create(
        "automation", "test", "log_bed_light", suggested_object_id="log_bed_light", original_name="Log Bed Light"
    )
    hass.states.async_set(entry.entity_id, "on", {ATTR_FRIENDLY_NAME: "Log Bed Light"})
    async_expose_entity(hass, ASSISTANT, entry.entity_id, True)
    return async_mock_service(hass, "automation", "trigger")


@pytest.mark.parametrize("sentence", ["run Log Bed Light", "trigger the Log Bed Light automation"])
@pytest.mark.usefixtures("manager")
async def test_sentence_triggers_the_automation(
    hass: HomeAssistant, home: Assist, trigger_calls: list[ServiceCall], sentence: str
) -> None:
    assert await say(hass, home, sentence) == "Triggered Log Bed Light"
    assert [call.data["entity_id"] for call in trigger_calls] == [[AUTOMATION]]


@pytest.mark.usefixtures("manager")
async def test_unknown_name_is_left_to_the_stock_agent(
    hass: HomeAssistant, home: Assist, trigger_calls: list[ServiceCall]
) -> None:
    speech = await say(hass, home, "run Nothing Called This")
    assert speech != "Triggered Nothing Called This"
    assert not trigger_calls


@pytest.mark.usefixtures("trigger_calls")
async def test_scheduled_run_stores_an_intent_job(hass: HomeAssistant, home: Assist, manager: JobManager) -> None:
    assert "trigger Log Bed Light" in await say(hass, home, "in 30 minutes run Log Bed Light")
    (job,) = manager.pending()
    assert job.kind is JobKind.INTENT
    assert job.intent is not None
    assert job.intent.type == "AutomationRun"
    assert job.targets.entity_ids == [AUTOMATION]
