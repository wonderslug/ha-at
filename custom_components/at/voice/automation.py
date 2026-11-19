"""The AutomationRun intent: trigger an exposed automation now or from a stored job."""

import probatio

from custom_components.at.const import INTENT_AUTOMATION_RUN
from custom_components.at.lang import get_language_pack, message
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, intent

ASSISTANT = "conversation"
AUTOMATION_DOMAIN = "automation"


def match_automations(hass: HomeAssistant, name: str) -> intent.MatchTargetsResult:
    """Find the exposed automations a spoken name refers to."""
    return intent.async_match_targets(
        hass,
        _constraints(name),
        intent.MatchTargetsPreferences(),
    )


def _constraints(name: str) -> intent.MatchTargetsConstraints:
    return intent.MatchTargetsConstraints(name=name, domains={AUTOMATION_DOMAIN}, assistant=ASSISTANT)


class AutomationRunHandler(intent.IntentHandler):
    """Trigger an automation by name; Home Assistant's own sentences only turn one on or off."""

    intent_type = INTENT_AUTOMATION_RUN
    description = "Runs an automation by name, skipping its conditions"

    @property
    def slot_schema(self) -> dict:
        """The automation's spoken name."""
        return {probatio.Required("name"): cv.string}

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Trigger every exposed automation the name matches."""
        slots = self.async_validate_slots(intent_obj.slots)
        name = slots["name"]["value"]
        constraints = _constraints(name)
        match = intent.async_match_targets(intent_obj.hass, constraints, intent.MatchTargetsPreferences())
        if not match.is_match:
            raise intent.MatchFailedError(match, constraints)
        await intent_obj.hass.services.async_call(
            AUTOMATION_DOMAIN,
            "trigger",
            {"entity_id": [state.entity_id for state in match.states]},
            blocking=True,
            context=intent_obj.context,
        )
        pack = get_language_pack(intent_obj.language)
        joiner = pack.joiner if pack else " and "
        response = intent_obj.create_response()
        response.async_set_speech(
            message(pack, "automation_triggered", name=joiner.join(state.name for state in match.states))
        )
        return response
