"""The at intents offered as tools of the Assist LLM API."""

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.at.core.models import JobStatus, Via
from custom_components.at.voice.intents import AtCancelHandler, AtListHandler, AtScheduleHandler
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import entity_registry as er, intent, llm
from tests.assist import ASSISTANT, LANGUAGE, Assist  # noqa: TID251  (plain module; see tests/assist.py)

pytestmark = [
    pytest.mark.real_dependencies,
    pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning"),
]


@pytest.fixture
async def api(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    assist: Assist,
    entity_registry: er.EntityRegistry,
    config_entry: MockConfigEntry,
) -> llm.APIInstance:
    """Load the integration with an exposed porch light and return the Assist LLM API."""
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
    context = llm.LLMContext(
        platform="test", context=Context(), language=LANGUAGE, assistant=ASSISTANT, device_id=assist.device_id
    )
    return await llm.async_get_api(hass, llm.LLM_API_ASSIST, context)


async def test_at_intents_exposed_as_llm_tools(api: llm.APIInstance) -> None:
    """All three at tools are offered with their descriptions."""
    tools = {tool.name: tool for tool in api.tools}
    assert tools["at__AtSchedule"].description == AtScheduleHandler.description
    assert tools["at__AtList"].description == AtListHandler.description
    assert tools["at__AtCancel"].description == AtCancelHandler.description


async def test_schedule_tool_creates_llm_job(api: llm.APIInstance, config_entry: MockConfigEntry) -> None:
    """Scheduling through the tool records Via.LLM and returns the confirmation speech."""
    result = await api.async_call_tool(
        llm.ToolInput(
            tool_name="at__AtSchedule",
            tool_args={"time": "in 20 minutes", "command": "turn on the porch light"},
        )
    )
    assert result.data["response_type"] == "action_done"
    assert result.data["speech"]["plain"]["speech"]
    (job,) = config_entry.runtime_data.manager.pending()
    assert job.status == JobStatus.PENDING
    assert job.source.via == Via.LLM


async def test_cancel_tool_with_no_query_cancels_nothing(api: llm.APIInstance, config_entry: MockConfigEntry) -> None:
    """An empty cancel call must not cancel anything."""
    await api.async_call_tool(
        llm.ToolInput(
            tool_name="at__AtSchedule",
            tool_args={"time": "in 20 minutes", "command": "turn on the porch light"},
        )
    )
    result = await api.async_call_tool(llm.ToolInput(tool_name="at__AtCancel", tool_args={}))
    assert result.data["speech"]["plain"]["speech"]
    assert len(config_entry.runtime_data.manager.pending()) == 1


async def test_list_tool_returns_speech(api: llm.APIInstance) -> None:
    """Listing through the tool returns the list speech."""
    await api.async_call_tool(
        llm.ToolInput(
            tool_name="at__AtSchedule",
            tool_args={"time": "in 20 minutes", "command": "turn on the porch light"},
        )
    )
    result = await api.async_call_tool(llm.ToolInput(tool_name="at__AtList", tool_args={}))
    assert "porch" in result.data["speech"]["plain"]["speech"].lower()


async def test_tool_parameters_accept_schedule_args(api: llm.APIInstance) -> None:
    """The tool's schema accepts the arguments the description promises."""
    tool = next(tool for tool in api.tools if tool.name == "at__AtSchedule")
    tool.parameters({"time": "in 20 minutes", "command": "turn on the porch light"})


async def test_list_tool_rejects_bogus_scope(api: llm.APIInstance, config_entry: MockConfigEntry) -> None:
    """An out-of-range scope is refused and nothing changes."""
    with pytest.raises(intent.InvalidSlotInfo):
        await api.async_call_tool(llm.ToolInput(tool_name="at__AtList", tool_args={"scope": "bogus"}))
    assert config_entry.runtime_data.manager.pending() == []


async def test_cancel_tool_rejects_non_bool_all(api: llm.APIInstance, config_entry: MockConfigEntry) -> None:
    """all must be a real boolean; a string cancels nothing."""
    await api.async_call_tool(
        llm.ToolInput(
            tool_name="at__AtSchedule",
            tool_args={"time": "in 20 minutes", "command": "turn on the porch light"},
        )
    )
    with pytest.raises(intent.InvalidSlotInfo):
        await api.async_call_tool(llm.ToolInput(tool_name="at__AtCancel", tool_args={"all": "yes"}))
    assert len(config_entry.runtime_data.manager.pending()) == 1
