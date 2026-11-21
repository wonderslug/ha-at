"""A command is checked against the targets its own intent handler will accept when the job fires."""

from dataclasses import dataclass

import pytest

from custom_components.at.ha_internal.recognize import RecognizedCommand, RecognizeError, async_recognize_command
from custom_components.at.lang import get_language_pack
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.components.media_player.const import MediaPlayerEntityFeature
from homeassistant.components.vacuum.const import VacuumEntityFeature
from homeassistant.const import ATTR_FRIENDLY_NAME, ATTR_SUPPORTED_FEATURES
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er
from homeassistant.setup import async_setup_component
from tests.assist import ASSISTANT, LANGUAGE, Assist  # noqa: TID251  (plain module; see tests/assist.py)

pytestmark = [
    pytest.mark.real_dependencies,
    pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning"),
]

PACK = get_language_pack(LANGUAGE)
assert PACK is not None

SPEAKER_FEATURES = (
    MediaPlayerEntityFeature.SEARCH_MEDIA | MediaPlayerEntityFeature.PLAY_MEDIA | MediaPlayerEntityFeature.PAUSE
)
CLEANER_FEATURES = VacuumEntityFeature.START | VacuumEntityFeature.CLEAN_AREA


@dataclass
class House:
    """The ids the tests assert on."""

    kitchen_area_id: str
    hallway_area_id: str


@pytest.fixture
async def house(
    hass: HomeAssistant, assist: Assist, area_registry: ar.AreaRegistry, entity_registry: er.EntityRegistry
) -> House:
    """
    Add a kitchen with a light and a speaker, a hallway with only a light, a radio, a vacuum and a list.

    The speaker is off and the vacuum is in no area: neither may stop a command from being scheduled.
    """
    for domain in ("media_player", "vacuum", "todo"):
        assert await async_setup_component(hass, domain, {})
    kitchen = area_registry.async_create("Kitchen")
    hallway = area_registry.async_create("Hallway")
    for domain, object_id, name, state, features, area_id in (
        ("light", "kitchen_ceiling", "Kitchen ceiling", "off", 0, kitchen.id),
        ("light", "hallway", "Hallway light", "off", 0, hallway.id),
        ("media_player", "kitchen_speaker", "Kitchen speaker", "off", SPEAKER_FEATURES, kitchen.id),
        ("media_player", "radio", "Radio", "playing", MediaPlayerEntityFeature.PLAY_MEDIA, None),
        ("vacuum", "robot", "Robot", "docked", CLEANER_FEATURES, None),
        ("todo", "groceries", "Groceries", "0", 0, None),
        ("cover", "kitchen_window", "Kitchen window", "closed", 0, None),
        ("lock", "front_door", "Front door", "unlocked", 0, None),
    ):
        entry = entity_registry.async_get_or_create(
            domain, "test", object_id, suggested_object_id=object_id, original_name=name
        )
        entity_registry.async_update_entity(entry.entity_id, area_id=area_id)
        hass.states.async_set(entry.entity_id, state, {ATTR_FRIENDLY_NAME: name, ATTR_SUPPORTED_FEATURES: features})
        async_expose_entity(hass, ASSISTANT, entry.entity_id, True)
    await hass.async_block_till_done()
    return House(kitchen_area_id=kitchen.id, hallway_area_id=hallway.id)


async def recognize(hass: HomeAssistant, text: str) -> RecognizedCommand:
    assert PACK is not None
    return await async_recognize_command(
        hass, text, language=LANGUAGE, device_id=None, satellite_id=None, context=Context(), pack=PACK
    )


@pytest.mark.usefixtures("house")
async def test_play_in_an_area_targets_only_its_player(hass: HomeAssistant) -> None:
    command = await recognize(hass, "play jazz in the kitchen")

    assert command.intent.type == "HassMediaSearchAndPlay"
    assert command.targets.entity_ids == ["media_player.kitchen_speaker"]


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("play jazz in the hallway", id="area-without-a-player"),
        pytest.param("play jazz on the radio", id="player-that-cannot-search"),
    ],
)
@pytest.mark.usefixtures("house")
async def test_play_without_a_searching_player_is_no_target(hass: HomeAssistant, text: str) -> None:
    with pytest.raises(RecognizeError) as err:
        await recognize(hass, text)

    assert err.value.code == "no_target"


@pytest.mark.usefixtures("house")
async def test_feature_required_by_a_service_intent(hass: HomeAssistant) -> None:
    with pytest.raises(RecognizeError) as err:
        await recognize(hass, "pause the radio")

    assert err.value.code == "no_target"


@pytest.mark.usefixtures("house")
async def test_state_required_by_a_service_intent_is_not_checked(hass: HomeAssistant) -> None:
    """The speaker is off now; whether it is playing is for fire time to find out."""
    command = await recognize(hass, "pause the kitchen speaker")

    assert command.intent.type == "HassMediaPause"
    assert command.targets.entity_ids == ["media_player.kitchen_speaker"]


async def test_clean_area_targets_a_vacuum_outside_the_area(hass: HomeAssistant, house: House) -> None:
    command = await recognize(hass, "vacuum the hallway")

    assert command.intent.type == "HassVacuumCleanArea"
    assert command.targets.entity_ids == ["vacuum.robot"]
    assert command.targets.area_ids == [house.hallway_area_id]


@pytest.mark.usefixtures("house")
async def test_clean_area_without_an_area_cleaner_is_no_target(hass: HomeAssistant) -> None:
    hass.states.async_set(
        "vacuum.robot", "docked", {ATTR_FRIENDLY_NAME: "Robot", ATTR_SUPPORTED_FEATURES: VacuumEntityFeature.START}
    )

    with pytest.raises(RecognizeError) as err:
        await recognize(hass, "vacuum the hallway")

    assert err.value.code == "no_target"


@pytest.mark.parametrize(
    ("text", "summary"),
    [
        pytest.param("play jazz in the kitchen", "Play jazz on Kitchen speaker", id="play-in-area"),
        pytest.param("play jazz on the kitchen speaker", "Play jazz on Kitchen speaker", id="play-on-player"),
        pytest.param("vacuum the hallway", "Clean Hallway", id="clean-area"),
        pytest.param("add milk to the groceries list", "Add milk to Groceries", id="list-add"),
        pytest.param("check off milk on the groceries list", "Check off milk on Groceries", id="list-complete"),
        pytest.param("remove milk from the groceries list", "Remove milk from Groceries", id="list-remove"),
        pytest.param("open the kitchen window", "Open Kitchen window", id="cover-open"),
        pytest.param("close the kitchen window", "Close Kitchen window", id="cover-close"),
        pytest.param("lock the front door", "Lock Front door", id="lock"),
        pytest.param("unlock the front door", "Unlock Front door", id="unlock"),
    ],
)
@pytest.mark.usefixtures("house")
async def test_summary(hass: HomeAssistant, text: str, summary: str) -> None:
    command = await recognize(hass, text)

    assert command.summary == summary


@pytest.mark.usefixtures("house")
async def test_list_item_targets_the_list(hass: HomeAssistant) -> None:
    command = await recognize(hass, "add milk to the groceries list")

    assert command.intent.type == "HassListAddItem"
    assert command.targets.entity_ids == ["todo.groceries"]
