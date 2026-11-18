"""Constants and the result type of the shared `assist` fixture (tests/conftest.py)."""

from dataclasses import dataclass

from homeassistant.components import conversation
from homeassistant.core import ServiceCall

ASSISTANT = conversation.DOMAIN
LANGUAGE = "en"


@dataclass
class Assist:
    """What the voice tests share: a satellite in the office and two lights."""

    device_id: str
    turn_on_calls: list[ServiceCall]
