"""The at.* service actions."""

from datetime import UTC, datetime, timedelta

from freezegun.api import FrozenDateTimeFactory
import probatio
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.at.const import DOMAIN
from custom_components.at.core.manager import JobManager
from custom_components.at.core.models import Job, JobKind, JobStatus, Result, Source, Targets, Via, new_job_id
from homeassistant.auth.models import User
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers import entity_registry as er
from tests.assist import ASSISTANT, Assist  # noqa: TID251  (plain module; see tests/assist.py)

pytestmark = [
    pytest.mark.real_dependencies,
    pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning"),
]

ACTION = [{"action": "light.turn_on", "target": {"entity_id": "light.porch"}}]


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


async def call(hass: HomeAssistant, service: str, data: dict, user: User | None = None):
    return await hass.services.async_call(
        DOMAIN,
        service,
        data,
        blocking=True,
        return_response=service != "run_now",
        context=Context(user_id=user.id if user else None),
    )


def make_job(due: datetime, *, status: JobStatus = JobStatus.PENDING, raw_action: bool = False, via: Via = Via.VOICE):
    return Job(
        id=new_job_id(),
        kind=JobKind.ACTION,
        status=status,
        due=due,
        created_at=due,
        finished_at=None if status is JobStatus.PENDING else due,
        summary="Turn on Porch Light",
        original_text=None,
        intent=None,
        action=ACTION,
        raw_action=raw_action,
        targets=Targets(),
        source=Source(via=via),
        result=Result(),
    )


async def test_schedule_command_with_when(hass: HomeAssistant, manager: JobManager) -> None:
    """A command with a `when` phrase becomes a service-sourced intent job."""
    response = await call(hass, "schedule", {"command": "turn on the porch light", "when": "at 11 pm"})
    assert response["summary"] == "Turn on Porch Light"
    assert response["due"] == "2026-11-18T05:00:00+00:00"
    job = manager.get(response["job_id"])
    assert job.kind is JobKind.INTENT
    assert job.source.via is Via.SERVICE


async def test_schedule_command_name_overrides_summary(hass: HomeAssistant, manager: JobManager) -> None:
    """`name` replaces the generated summary."""
    response = await call(
        hass, "schedule", {"command": "turn on the porch light", "delay": {"minutes": 5}, "name": "Porch"}
    )
    assert response["summary"] == "Porch"
    assert manager.get(response["job_id"]).summary == "Porch"
    assert response["due"] == "2026-11-18T04:27:00+00:00"


async def test_schedule_command_refused(hass: HomeAssistant, manager: JobManager) -> None:
    """A command that can't be scheduled raises a validation error carrying the speech."""
    with pytest.raises(ServiceValidationError, match="Sorry"):
        await call(hass, "schedule", {"command": "turn on the porch light", "when": "gibberish"})
    assert not manager.pending()


async def test_schedule_action_with_delay(hass: HomeAssistant, manager: JobManager) -> None:
    """A raw action with a delay is stored as a raw_action job."""
    response = await call(hass, "schedule", {"action": ACTION, "delay": {"hours": 1}})
    assert response["due"] == "2026-11-18T05:22:00+00:00"
    assert response["summary"] == "Turn on Porch Light"
    job = manager.get(response["job_id"])
    assert job.kind is JobKind.ACTION
    assert job.raw_action is True
    assert job.targets.entity_ids == ["light.porch"]
    assert job.source.via is Via.SERVICE


async def test_schedule_action_with_at_and_name(hass: HomeAssistant, manager: JobManager) -> None:
    """`at` is taken as given and `name` is the summary."""
    response = await call(
        hass, "schedule", {"action": ACTION, "at": "2026-11-19T10:00:00+00:00", "name": "Morning light"}
    )
    assert response["due"] == "2026-11-19T10:00:00+00:00"
    assert response["summary"] == "Morning light"


async def test_schedule_action_with_when(hass: HomeAssistant, manager: JobManager) -> None:
    """`when` is parsed in the Home Assistant time zone."""
    response = await call(hass, "schedule", {"action": ACTION, "when": "at 11 pm"})
    assert response["due"] == "2026-11-18T05:00:00+00:00"


async def test_schedule_action_bad_when(hass: HomeAssistant, manager: JobManager) -> None:
    """An unparsable `when` is a validation error."""
    with pytest.raises(ServiceValidationError):
        await call(hass, "schedule", {"action": ACTION, "when": "someday"})


@pytest.mark.parametrize(
    "data",
    [
        {"command": "x", "action": ACTION, "delay": {"minutes": 1}},
        {"command": "turn on the porch light"},
        {"command": "x", "at": "2026-11-19T10:00:00+00:00", "delay": {"minutes": 1}},
        {"action": ACTION, "delay": {"minutes": 1}, "when": "in 5 minutes"},
        {"action": ACTION},
        {},
    ],
)
async def test_schedule_requires_exactly_one_time_field(hass: HomeAssistant, manager: JobManager, data: dict) -> None:
    """Both-or-neither of the exclusive field groups fails validation."""
    with pytest.raises(probatio.Invalid):
        await call(hass, "schedule", data)


async def test_schedule_raw_action_non_admin_unauthorized(
    hass: HomeAssistant, manager: JobManager, hass_read_only_user: User
) -> None:
    """A non-admin user can't schedule a raw action."""
    with pytest.raises(Unauthorized):
        await call(hass, "schedule", {"action": ACTION, "delay": {"minutes": 1}}, hass_read_only_user)
    assert not manager.pending()


async def test_schedule_raw_action_admin_ok(hass: HomeAssistant, manager: JobManager, hass_admin_user: User) -> None:
    """An admin can."""
    response = await call(hass, "schedule", {"action": ACTION, "delay": {"minutes": 1}}, hass_admin_user)
    assert manager.get(response["job_id"]).source.user_id == hass_admin_user.id


async def test_schedule_raw_action_from_automation_context_ok(hass: HomeAssistant, manager: JobManager) -> None:
    """A call with no user (an automation) is allowed."""
    response = await call(hass, "schedule", {"action": ACTION, "delay": {"minutes": 1}})
    assert manager.get(response["job_id"]).raw_action is True


async def test_schedule_without_entry(hass: HomeAssistant) -> None:
    """With no entry loaded the action explains why instead of failing obscurely."""
    from custom_components.at.service_actions import async_setup_services  # noqa: PLC0415

    async_setup_services(hass)
    with pytest.raises(ServiceValidationError):
        await call(hass, "clear_history", {})


async def test_list_response(hass: HomeAssistant, manager: JobManager) -> None:
    """Pending and history come back as job dicts, filtered by status and range."""
    now = datetime(2026, 11, 18, 4, 22, tzinfo=UTC)
    soon = await manager.async_add(make_job(now + timedelta(hours=1)))
    later = await manager.async_add(make_job(now + timedelta(days=2)))
    done = await manager.async_add(make_job(now + timedelta(hours=2)))
    await manager.async_cancel(done.id, "voice")

    response = await call(hass, "list", {})
    assert [j["id"] for j in response["pending"]] == [soon.id, later.id]
    assert [j["id"] for j in response["history"]] == [done.id]
    assert response["pending"][0]["due"] == "2026-11-18T05:22:00+00:00"

    response = await call(hass, "list", {"status": ["cancelled"]})
    assert response["pending"] == []
    assert [j["id"] for j in response["history"]] == [done.id]

    response = await call(hass, "list", {"end": "2026-11-19T00:00:00+00:00"})
    assert [j["id"] for j in response["pending"]] == [soon.id]


async def test_cancel_by_id_and_all(hass: HomeAssistant, manager: JobManager) -> None:
    """Cancel by one id or a list, then `all` takes service-created jobs too."""
    now = datetime(2026, 11, 18, 4, 22, tzinfo=UTC)
    one = await manager.async_add(make_job(now + timedelta(hours=1)))
    two = await manager.async_add(make_job(now + timedelta(hours=2)))
    three = await manager.async_add(make_job(now + timedelta(hours=3), via=Via.SERVICE))
    four = await manager.async_add(make_job(now + timedelta(hours=4)))

    assert await call(hass, "cancel", {"job_id": one.id}) == {"cancelled": [one.id]}
    assert await call(hass, "cancel", {"job_id": [two.id]}) == {"cancelled": [two.id]}
    response = await call(hass, "cancel", {"all": True})
    assert sorted(response["cancelled"]) == sorted([three.id, four.id])
    assert not manager.pending()


async def test_cancel_requires_one_selector(hass: HomeAssistant, manager: JobManager) -> None:
    """Neither or both of job_id and all is invalid."""
    with pytest.raises(probatio.Invalid):
        await call(hass, "cancel", {})
    with pytest.raises(probatio.Invalid):
        await call(hass, "cancel", {"job_id": "abc", "all": True})


async def test_run_now(hass: HomeAssistant, manager: JobManager) -> None:
    """run_now launches a pending job."""
    job = await manager.async_add(make_job(datetime(2026, 11, 19, tzinfo=UTC)))
    await call(hass, "run_now", {"job_id": job.id})
    await hass.async_block_till_done()
    assert manager.get(job.id).status is not JobStatus.PENDING


async def test_run_now_raw_action_non_admin_unauthorized(
    hass: HomeAssistant, manager: JobManager, hass_read_only_user: User
) -> None:
    """A non-admin can't run a raw action early."""
    job = await manager.async_add(make_job(datetime(2026, 11, 19, tzinfo=UTC), raw_action=True))
    with pytest.raises(Unauthorized):
        await call(hass, "run_now", {"job_id": job.id}, hass_read_only_user)
    assert manager.get(job.id).status is JobStatus.PENDING


async def test_clear_history(hass: HomeAssistant, manager: JobManager) -> None:
    """clear_history removes finished jobs and reports how many."""
    now = datetime(2026, 11, 18, 4, 22, tzinfo=UTC)
    job = await manager.async_add(make_job(now + timedelta(hours=1)))
    await manager.async_cancel(job.id, "voice")
    assert await call(hass, "clear_history", {}) == {"removed": 1}
    assert manager.history() == []


@pytest.mark.parametrize("service", ["cancel", "run_now"])
async def test_unknown_job_is_translated(hass: HomeAssistant, manager: JobManager, service: str) -> None:
    """An unknown id is a translated validation error."""
    with pytest.raises(ServiceValidationError) as err:
        await call(hass, service, {"job_id": "nope"})
    assert err.value.translation_key == "job_not_found"
    assert err.value.translation_placeholders == {"job_id": "nope"}


@pytest.mark.parametrize("service", ["cancel", "run_now"])
async def test_finished_job_is_translated(hass: HomeAssistant, manager: JobManager, service: str) -> None:
    """A job that is no longer pending is a translated validation error."""
    job = await manager.async_add(make_job(datetime(2026, 11, 19, tzinfo=UTC)))
    await manager.async_cancel(job.id, "voice")
    with pytest.raises(ServiceValidationError) as err:
        await call(hass, service, {"job_id": job.id})
    assert err.value.translation_key == "job_not_pending"
