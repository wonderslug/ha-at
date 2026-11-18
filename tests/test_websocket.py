"""The at/* websocket commands."""

from datetime import UTC, datetime
from typing import Any

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.at.core.manager import JobManager
from custom_components.at.core.models import JobKind, JobStatus, Via
from homeassistant.auth.models import User
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from tests.assist import ASSISTANT, Assist  # noqa: TID251  (plain module; see tests/assist.py)
from tests.test_services import ACTION, make_job  # noqa: TID251

pytestmark = [
    pytest.mark.real_dependencies,
    pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning"),
]

RAW_ACTION = [{"action": "light.turn_on", "target": {"entity_id": "light.porch"}, "data": {"brightness": 5}}]
DUE = datetime(2026, 11, 19, 10, 0, tzinfo=UTC)

type Client = Any


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


@pytest.fixture
async def admin_client(hass: HomeAssistant, manager: JobManager, hass_ws_client: WebSocketGenerator) -> Client:
    """A websocket client for an administrator."""
    return await hass_ws_client(hass)


@pytest.fixture
async def user_client(
    hass: HomeAssistant, manager: JobManager, hass_ws_client: WebSocketGenerator, hass_read_only_user: User
) -> Client:
    """A websocket client for a non-administrator."""
    from pytest_homeassistant_custom_component.common import MockUser  # noqa: PLC0415

    assert isinstance(hass_read_only_user, MockUser)
    token = await hass.auth.async_create_refresh_token(hass_read_only_user, "https://example.com")
    access = hass.auth.async_create_access_token(token)
    return await hass_ws_client(hass, access)


async def send(client: Client, command: str, **fields: Any) -> dict[str, Any]:
    await client.send_json_auto_id({"type": f"at/{command}", **fields})
    return await client.receive_json()


async def test_subscribe_snapshot_then_changes(hass: HomeAssistant, manager: JobManager, admin_client: Client) -> None:
    """Subscribing sends the snapshot, then one event per change."""
    pending = make_job(DUE)
    await manager.async_add(pending)
    await admin_client.send_json_auto_id({"type": "at/subscribe"})
    result = await admin_client.receive_json()
    assert result["success"]
    snapshot = (await admin_client.receive_json())["event"]["snapshot"]
    assert [j["id"] for j in snapshot["pending"]] == [pending.id]
    assert snapshot["history"] == []
    assert snapshot["running"] == []

    await manager.async_cancel_many([pending.id], "test")
    event = (await admin_client.receive_json())["event"]
    assert event["change"]["kind"] == "updated"
    assert event["change"]["job"]["id"] == pending.id
    assert event["change"]["job"]["status"] == "cancelled"


async def test_subscribe_unsubscribes_on_unsubscribe(
    hass: HomeAssistant, manager: JobManager, admin_client: Client
) -> None:
    """Unsubscribing removes the manager subscription."""
    await admin_client.send_json_auto_id({"type": "at/subscribe"})
    sub_id = (await admin_client.receive_json())["id"]
    await admin_client.receive_json()
    assert len(manager._subscribers) >= 1  # noqa: SLF001
    before = len(manager._subscribers)  # noqa: SLF001
    await admin_client.send_json_auto_id({"type": "unsubscribe_events", "subscription": sub_id})
    assert (await admin_client.receive_json())["success"]
    assert len(manager._subscribers) == before - 1  # noqa: SLF001


async def test_parse_preview_no_job(hass: HomeAssistant, manager: JobManager, admin_client: Client) -> None:
    """Parsing previews a command and stores nothing."""
    response = await send(admin_client, "parse", text="turn on the porch light at 11 pm")
    assert response["success"]
    assert response["result"] == {"ok": True, "summary": "Turn on Porch Light", "due": "2026-11-18T05:00:00+00:00"}
    assert not manager.pending()


async def test_parse_refusal_message(hass: HomeAssistant, manager: JobManager, admin_client: Client) -> None:
    """A refusal is a normal result with ok false."""
    response = await send(admin_client, "parse", text="turn on the porch light at gibberish")
    assert response["success"]
    assert response["result"]["ok"] is False
    assert response["result"]["message"]


async def test_schedule_text(hass: HomeAssistant, manager: JobManager, admin_client: Client) -> None:
    """Text is scheduled as a panel job."""
    response = await send(admin_client, "schedule", text="turn on the porch light at 11 pm")
    assert response["success"]
    job = response["result"]["job"]
    assert job["summary"] == "Turn on Porch Light"
    assert job["source"]["via"] == "panel"
    assert manager.get(job["id"]).status is JobStatus.PENDING


async def test_schedule_text_refused(hass: HomeAssistant, manager: JobManager, admin_client: Client) -> None:
    """A refused command is a refused error."""
    response = await send(admin_client, "schedule", text="turn on the porch light at gibberish")
    assert not response["success"]
    assert response["error"]["code"] == "refused"
    assert not manager.pending()


async def test_schedule_picked_action_non_admin_ok(
    hass: HomeAssistant, manager: JobManager, user_client: Client
) -> None:
    """A non-admin may schedule an action that passes the allowlist."""
    response = await send(user_client, "schedule", action=ACTION, delay_seconds=3600)
    assert response["success"], response
    job = response["result"]["job"]
    assert job["raw_action"] is False
    assert job["kind"] == str(JobKind.ACTION)
    assert job["due"] == "2026-11-18T05:22:00+00:00"
    assert job["source"]["via"] == str(Via.PANEL)


async def test_schedule_raw_action_non_admin_unauthorized(
    hass: HomeAssistant, manager: JobManager, user_client: Client
) -> None:
    """A non-admin may not schedule an action outside the allowlist."""
    response = await send(user_client, "schedule", action=RAW_ACTION, delay_seconds=60)
    assert not response["success"]
    assert response["error"]["code"] == "unauthorized"
    assert not manager.pending()


async def test_schedule_raw_action_admin_ok_sets_raw_flag(
    hass: HomeAssistant, manager: JobManager, admin_client: Client
) -> None:
    """An admin's off-allowlist action is saved with raw_action set."""
    response = await send(admin_client, "schedule", action=RAW_ACTION, due="2026-11-19T10:00:00+00:00")
    assert response["success"], response
    assert response["result"]["job"]["raw_action"] is True
    assert response["result"]["job"]["due"] == "2026-11-19T10:00:00+00:00"


async def test_schedule_invalid_combination(hass: HomeAssistant, manager: JobManager, admin_client: Client) -> None:
    """An action without a time is invalid."""
    response = await send(admin_client, "schedule", action=ACTION)
    assert not response["success"]
    assert response["error"]["code"] == "invalid"


async def test_cancel_any_users_job(hass: HomeAssistant, manager: JobManager, user_client: Client) -> None:
    """A job created by someone else can be cancelled by a non-admin."""
    job = await manager.async_add(make_job(DUE))
    response = await send(user_client, "cancel", job_ids=[job.id])
    assert response["success"]
    assert response["result"] == {"cancelled": [job.id]}


async def test_cancel_errors(hass: HomeAssistant, manager: JobManager, admin_client: Client) -> None:
    """Unknown and finished jobs get stable error codes."""
    response = await send(admin_client, "cancel", job_ids=["nope"])
    assert response["error"]["code"] == "not_found"
    job = await manager.async_add(make_job(DUE))
    await manager.async_cancel_many([job.id], "test")
    response = await send(admin_client, "cancel", job_ids=[job.id])
    assert response["error"]["code"] == "not_pending"


async def test_run_now_raw_action_non_admin_unauthorized(
    hass: HomeAssistant, manager: JobManager, user_client: Client
) -> None:
    """A non-admin can't run a raw action."""
    job = await manager.async_add(make_job(DUE, raw_action=True))
    response = await send(user_client, "run_now", job_id=job.id)
    assert response["error"]["code"] == "unauthorized"
    assert manager.get(job.id).status is JobStatus.PENDING


async def test_run_now_picked_action(hass: HomeAssistant, manager: JobManager, user_client: Client) -> None:
    """A non-admin can run an allowlisted job now."""
    job = await manager.async_add(make_job(DUE))
    response = await send(user_client, "run_now", job_id=job.id)
    assert response["success"], response
    assert response["result"]["job"]["id"] == job.id


async def test_reschedule_copy(hass: HomeAssistant, manager: JobManager, user_client: Client) -> None:
    """Rescheduling queues a new copy."""
    job = await manager.async_add(make_job(DUE))
    response = await send(user_client, "reschedule", job_id=job.id, due="2026-11-20T10:00:00+00:00")
    assert response["success"], response
    copy = response["result"]["job"]
    assert copy["id"] != job.id
    assert copy["due"] == "2026-11-20T10:00:00+00:00"
    assert len(manager.pending()) == 2


async def test_reschedule_raw_action_non_admin_unauthorized(
    hass: HomeAssistant, manager: JobManager, user_client: Client
) -> None:
    """A non-admin can't copy a raw action."""
    job = await manager.async_add(make_job(DUE, raw_action=True))
    response = await send(user_client, "reschedule", job_id=job.id, due="2026-11-20T10:00:00+00:00")
    assert response["error"]["code"] == "unauthorized"
    assert len(manager.pending()) == 1


async def test_clear_history(hass: HomeAssistant, manager: JobManager, user_client: Client) -> None:
    """Anyone can clear the history."""
    job = await manager.async_add(make_job(DUE))
    await manager.async_cancel_many([job.id], "test")
    response = await send(user_client, "clear_history")
    assert response["result"] == {"removed": 1}


@pytest.mark.parametrize(
    ("config_entry", "expected"), [({}, False), ({"panel_admin_only": True}, True)], indirect=["config_entry"]
)
async def test_info_flags(
    hass: HomeAssistant,
    manager: JobManager,
    admin_client: Client,
    user_client: Client,
    expected: bool,
) -> None:
    """Info reports the caller's admin flag and the entry options."""
    assert (await send(admin_client, "info"))["result"] == {
        "is_admin": True,
        "panel_admin_only": expected,
        "language_supported": True,
    }
    assert (await send(user_client, "info"))["result"]["is_admin"] is False


async def test_not_loaded(hass: HomeAssistant, hass_ws_client: WebSocketGenerator) -> None:
    """Without a loaded entry every command says not_loaded."""
    from custom_components.at import async_setup  # noqa: PLC0415

    await async_setup(hass, {})
    client = await hass_ws_client(hass)
    response = await send(client, "info")
    assert response["error"]["code"] == "not_loaded"
