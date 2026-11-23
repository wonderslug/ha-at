"""Fixtures the voice sentence tests share: recorded broadcasts and announcements, and a stub LLM pipeline."""

from typing import override

import pytest
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.at.core.manager import JobManager
from homeassistant.components.assist_satellite.const import AssistSatelliteEntityFeature
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import area_registry as ar, entity_registry as er, intent
from tests.assist import StubLlmAgent, use_agent  # noqa: TID251  (plain module; see tests/assist.py)


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


@pytest.fixture
def announce_calls(
    hass: HomeAssistant, area_registry: ar.AreaRegistry, entity_registry: er.EntityRegistry
) -> list[ServiceCall]:
    """Put an announcing satellite in the office, beside the one spoken to, and record announcements."""
    office = area_registry.async_get_area_by_name("Office")
    assert office is not None
    entry = entity_registry.async_get_or_create(
        "assist_satellite",
        "test",
        "office_speaker",
        suggested_object_id="office_speaker",
        supported_features=AssistSatelliteEntityFeature.ANNOUNCE,
    )
    entity_registry.async_update_entity(entry.entity_id, area_id=office.id)
    hass.states.async_set(entry.entity_id, "idle")
    return async_mock_service(hass, "assist_satellite", "announce")


@pytest.fixture
async def llm_pipeline(hass: HomeAssistant, manager: JobManager) -> StubLlmAgent:
    """Make a stub LLM the pipeline's agent, with prefer-local on."""
    stub_agent = StubLlmAgent()
    await use_agent(hass, stub_agent)
    return stub_agent
