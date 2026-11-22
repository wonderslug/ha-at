"""A command is checked against the targets its own intent handler will accept when the job fires."""

from dataclasses import dataclass

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.at.ha_internal.recognize import RecognizedCommand, RecognizeError, async_recognize_command
from custom_components.at.lang import get_language_pack
from homeassistant.components.assist_satellite.const import AssistSatelliteEntityFeature
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.components.media_player.const import MediaPlayerEntityFeature
from homeassistant.components.vacuum.const import VacuumEntityFeature
from homeassistant.const import ATTR_FRIENDLY_NAME, ATTR_SUPPORTED_FEATURES
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
    floor_registry as fr,
)
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


async def recognize(
    hass: HomeAssistant, text: str, *, device_id: str | None = None, time_last: bool = False
) -> RecognizedCommand:
    assert PACK is not None
    return await async_recognize_command(
        hass,
        text,
        language=LANGUAGE,
        device_id=device_id,
        satellite_id=None,
        context=Context(),
        pack=PACK,
        time_last=time_last,
    )


def add_satellite(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    object_id: str,
    *,
    features: int = AssistSatelliteEntityFeature.ANNOUNCE,
    device_id: str | None = None,
    area_id: str | None = None,
) -> str:
    """Register a voice satellite; broadcasts do not need it exposed."""
    entry = entity_registry.async_get_or_create(
        "assist_satellite",
        "test",
        object_id,
        suggested_object_id=object_id,
        original_name=object_id.replace("_", " ").title(),
        supported_features=features,
        device_id=device_id,
    )
    entity_registry.async_update_entity(entry.entity_id, area_id=area_id)
    hass.states.async_set(entry.entity_id, "idle", {ATTR_SUPPORTED_FEATURES: features})
    return entry.entity_id


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


@pytest.mark.usefixtures("house")
async def test_broadcast_reaches_announcing_satellites(hass: HomeAssistant, entity_registry: er.EntityRegistry) -> None:
    kitchen = add_satellite(hass, entity_registry, "kitchen_satellite")
    add_satellite(hass, entity_registry, "mute_satellite", features=0)

    command = await recognize(hass, "broadcast dinner is ready")

    assert command.intent.type == "HassBroadcast"
    assert command.targets.entity_ids == [kitchen]
    assert command.summary == 'Broadcast "dinner is ready"'


@pytest.mark.usefixtures("house")
async def test_broadcast_without_an_announcing_satellite_is_no_target(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    add_satellite(hass, entity_registry, "mute_satellite", features=0)

    with pytest.raises(RecognizeError) as err:
        await recognize(hass, "broadcast dinner is ready")

    assert err.value.code == "no_target"


@pytest.mark.usefixtures("house")
async def test_broadcast_skips_the_satellite_it_was_spoken_to(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, device_registry: dr.DeviceRegistry
) -> None:
    """The handler leaves the speaking device out, so it alone cannot hear the broadcast."""
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(config_entry_id=entry.entry_id, identifiers={("test", "speaker")})
    add_satellite(hass, entity_registry, "speaking_satellite", device_id=device.id)

    with pytest.raises(RecognizeError) as err:
        await recognize(hass, "broadcast dinner is ready", device_id=device.id)

    assert err.value.code == "no_target"


@pytest.mark.usefixtures("house")
async def test_broadcast_with_its_time_after_the_message_is_refused(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """In "broadcast dinner is at 6" the time belongs to the message, so it is not a job."""
    add_satellite(hass, entity_registry, "kitchen_satellite")

    with pytest.raises(RecognizeError) as err:
        await recognize(hass, "broadcast dinner is", time_last=True)

    assert err.value.code == "refused"


async def test_announcement_to_an_area_reaches_only_its_satellites(
    hass: HomeAssistant, house: House, entity_registry: er.EntityRegistry
) -> None:
    kitchen = add_satellite(hass, entity_registry, "kitchen_satellite", area_id=house.kitchen_area_id)
    add_satellite(hass, entity_registry, "hallway_satellite", area_id=house.hallway_area_id)

    command = await recognize(hass, "announce in the kitchen that dinner is ready")

    assert command.intent.type == "PlaceAnnounce"
    assert command.intent.slots["area"]["value"] == house.kitchen_area_id
    assert command.targets.entity_ids == [kitchen]
    assert command.targets.area_ids == [house.kitchen_area_id]
    assert command.summary == 'Announce "dinner is ready" in Kitchen'


async def test_announcement_to_an_area_finds_a_satellite_by_its_device(
    hass: HomeAssistant, house: House, entity_registry: er.EntityRegistry, device_registry: dr.DeviceRegistry
) -> None:
    """The satellite spoken to is in the area too, and an announcement there includes it."""
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(config_entry_id=entry.entry_id, identifiers={("test", "speaker")})
    device_registry.async_update_device(device.id, area_id=house.kitchen_area_id)
    kitchen = add_satellite(hass, entity_registry, "speaking_satellite", device_id=device.id)

    command = await recognize(hass, "tell the kitchen dinner is ready", device_id=device.id)

    assert command.targets.entity_ids == [kitchen]


async def test_announcement_to_an_area_without_a_satellite_is_no_target(
    hass: HomeAssistant, house: House, entity_registry: er.EntityRegistry
) -> None:
    add_satellite(hass, entity_registry, "kitchen_satellite", area_id=house.kitchen_area_id)

    with pytest.raises(RecognizeError) as err:
        await recognize(hass, "let the hallway know dinner is ready")

    assert err.value.code == "no_target"


@pytest.mark.usefixtures("house")
async def test_announcement_to_an_unknown_area_is_a_broadcast(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """With no garage area, "in the garage" can only be part of the message, as Home Assistant reads it."""
    add_satellite(hass, entity_registry, "kitchen_satellite")

    command = await recognize(hass, "announce in the garage the car is ready")

    assert command.intent.type == "HassBroadcast"
    assert command.intent.slots["message"]["value"] == "in the garage the car is ready"


async def test_announcement_to_an_area_with_its_time_after_the_message_is_refused(
    hass: HomeAssistant, house: House, entity_registry: er.EntityRegistry
) -> None:
    add_satellite(hass, entity_registry, "kitchen_satellite", area_id=house.kitchen_area_id)

    with pytest.raises(RecognizeError) as err:
        await recognize(hass, "announce in the kitchen dinner is", time_last=True)

    assert err.value.code == "refused"


@pytest.fixture
def floors(
    hass: HomeAssistant,
    house: House,
    area_registry: ar.AreaRegistry,
    floor_registry: fr.FloorRegistry,
    entity_registry: er.EntityRegistry,
) -> dict[str, str]:
    """Put the kitchen downstairs and the hallway upstairs, with a satellite only in the kitchen."""
    downstairs = floor_registry.async_create("Downstairs", aliases={"ground floor"})
    upstairs = floor_registry.async_create("Upstairs")
    area_registry.async_update(house.kitchen_area_id, floor_id=downstairs.floor_id)
    area_registry.async_update(house.hallway_area_id, floor_id=upstairs.floor_id)
    kitchen = add_satellite(hass, entity_registry, "kitchen_satellite", area_id=house.kitchen_area_id)
    return {"downstairs": downstairs.floor_id, "upstairs": upstairs.floor_id, "satellite": kitchen}


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("announce downstairs dinner is ready", id="bare-floor"),
        pytest.param("broadcast on the ground floor that dinner is ready", id="alias"),
        pytest.param("tell everyone downstairs dinner is ready", id="tell-everyone"),
        pytest.param("let everybody on the ground floor know dinner is ready", id="let-know"),
    ],
)
async def test_announcement_to_a_floor_reaches_its_satellites(
    hass: HomeAssistant, floors: dict[str, str], text: str
) -> None:
    command = await recognize(hass, text)

    assert command.intent.type == "PlaceAnnounce"
    assert command.intent.slots["floor"]["value"] == floors["downstairs"]
    assert command.targets.entity_ids == [floors["satellite"]]
    assert command.targets.floor_ids == [floors["downstairs"]]
    assert command.summary == 'Announce "dinner is ready" on Downstairs'


@pytest.mark.usefixtures("floors")
async def test_announcement_to_a_floor_without_a_satellite_is_no_target(hass: HomeAssistant) -> None:
    with pytest.raises(RecognizeError) as err:
        await recognize(hass, "announce upstairs dinner is ready")

    assert err.value.code == "no_target"
    assert "Upstairs" in err.value.message


async def test_a_name_both_an_area_and_a_floor_use_means_the_area(
    hass: HomeAssistant, house: House, floors: dict[str, str], floor_registry: fr.FloorRegistry
) -> None:
    floor_registry.async_update(floors["downstairs"], name="Kitchen")

    command = await recognize(hass, "announce to the kitchen dinner is ready")

    assert command.intent.slots["area"]["value"] == house.kitchen_area_id
    assert "floor" not in command.intent.slots


@pytest.mark.parametrize(
    "text",
    [
        "tell everyone dinner is ready",
        "tell everybody that dinner is ready",
        "let everyone know dinner is ready",
        "announce to everyone that dinner is ready",
        "broadcast to the house dinner is ready",
    ],
)
@pytest.mark.usefixtures("house")
async def test_broadcast_in_other_words(hass: HomeAssistant, entity_registry: er.EntityRegistry, text: str) -> None:
    add_satellite(hass, entity_registry, "kitchen_satellite")

    command = await recognize(hass, text)

    assert command.intent.type == "HassBroadcast"
    assert command.summary == 'Broadcast "dinner is ready"'


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
