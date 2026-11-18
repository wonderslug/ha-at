"""Constants and the result type of the shared `assist` fixture (tests/conftest.py)."""

from dataclasses import dataclass

from homeassistant.components import conversation
from homeassistant.core import Context, HomeAssistant, ServiceCall

ASSISTANT = conversation.DOMAIN
LANGUAGE = "en"
LIGHT = "light.master_bathroom"


@dataclass
class Assist:
    """What the voice tests share: a satellite in the office and two lights."""

    device_id: str
    turn_on_calls: list[ServiceCall]


async def say(hass: HomeAssistant, home: Assist, text: str) -> str:
    result = await conversation.async_converse(hass, text, None, Context(), LANGUAGE, device_id=home.device_id)
    return result.response.speech["plain"]["speech"]
