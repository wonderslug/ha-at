"""To-do list of the scheduled jobs."""

from datetime import datetime
from typing import TYPE_CHECKING

from custom_components.at.const import DOMAIN
from custom_components.at.core.errors import JobNotFound, JobStateError
from custom_components.at.core.models import Job, JobStatus, Via
from custom_components.at.core.timeparse import TimeParseError, split_time_and_command
from custom_components.at.entity.base import AtEntity
from custom_components.at.lang import LanguagePack, get_language_pack
from custom_components.at.lang.en import EN
from custom_components.at.service_actions.common import async_require_admin, job_not_pending
from custom_components.at.voice.scheduling import ScheduleRefused, async_schedule_command
from homeassistant.components.todo.const import TodoItemStatus, TodoListEntityFeature
from homeassistant.components.todo.entity import TodoItem, TodoListEntity
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity import EntityDescription

if TYPE_CHECKING:
    from custom_components.at.data import AtConfigEntry


ENTITY_DESCRIPTION = EntityDescription(key="scheduled", translation_key="scheduled", name=None)


class AtScheduledTodo(AtEntity, TodoListEntity):
    """Pending jobs as open items and finished jobs as completed ones."""

    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.SET_DUE_DATETIME_ON_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    def __init__(self, entry: AtConfigEntry) -> None:
        """Initialize the to-do list."""
        super().__init__(entry, ENTITY_DESCRIPTION)
        # Pin the id: the device name would otherwise yield todo.scheduled_jobs.
        self.entity_id = "todo.at_scheduled"

    @property
    def _pack(self) -> LanguagePack:
        return get_language_pack(self.hass.config.language) or EN

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return pending jobs by due time, then history, newest first. Running jobs are not listed."""
        pack = self._pack
        pending = [
            TodoItem(uid=job.id, summary=job.summary, status=TodoItemStatus.NEEDS_ACTION, due=job.due)
            for job in self._manager.pending()
        ]
        history = [
            TodoItem(
                uid=job.id,
                summary=job.summary,
                status=TodoItemStatus.COMPLETED,
                due=job.due,
                description=_describe(pack, job),
            )
            for job in self._manager.history()
        ]
        return pending + history

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Schedule the command in the summary, at the time in it or the due time."""
        manager = self._manager
        pack = self._pack
        summary = item.summary or ""
        due = item.due if isinstance(item.due, datetime) else None
        if due is not None:
            # A time phrase in the text wins over the due field only when there is one.
            try:
                split_time_and_command(summary, pack)
            except TimeParseError:
                pass
            else:
                due = None
        try:
            outcome = await async_schedule_command(
                self.hass,
                manager,
                command_text=summary,
                time_text=None,
                language=self.hass.config.language,
                via=Via.TODO,
                user_id=self._context.user_id if self._context else None,
                device_id=None,
                satellite_id=None,
                due=due,
                dry_run=True,
            )
        except ScheduleRefused as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="schedule_refused",
                translation_placeholders={"speech": err.speech},
            ) from err
        await manager.async_add(outcome.job)

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Move a pending job, or run it now when it is marked completed; a finished job can't be moved or reopened."""
        uid = item.uid or ""
        job = self._get(uid)
        if item.summary is not None and item.summary != job.summary:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="summary_not_editable")
        if job.status is not JobStatus.PENDING:
            moved = isinstance(item.due, datetime) and item.due != job.due
            if moved or item.status == TodoItemStatus.NEEDS_ACTION:
                raise job_not_pending(uid)
            return
        move = isinstance(item.due, datetime) and item.due != job.due
        run = item.status == TodoItemStatus.COMPLETED
        if job.raw_action and (move or run):
            await async_require_admin(self.hass, self._context)
        try:
            if move and isinstance(item.due, datetime):
                await self._manager.async_set_due(uid, item.due)
            if run:
                await self._manager.async_run_now(uid)
        except JobStateError as err:
            raise job_not_pending(uid) from err

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Cancel pending jobs and delete finished ones."""
        jobs = [self._get(uid) for uid in uids]
        pending = [job.id for job in jobs if job.status is JobStatus.PENDING]
        finished = [job.id for job in jobs if job.status is not JobStatus.PENDING]
        try:
            if pending:
                await self._manager.async_cancel_many(pending, str(Via.TODO), self._context)
            if finished:
                await self._manager.async_delete_history(finished)
        except JobStateError as err:
            raise job_not_pending(", ".join(uids)) from err

    def _get(self, job_id: str) -> Job:
        try:
            return self._manager.get(job_id)
        except JobNotFound as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="job_not_found", translation_placeholders={"job_id": job_id}
            ) from err


def _describe(pack: LanguagePack, job: Job) -> str:
    words = pack.todo
    match job.status:
        case JobStatus.FAILED if job.result.error:
            return words["failed"].format(error=job.result.error)
        case JobStatus.FAILED:
            return words["failed_no_error"]
        case JobStatus.MISSED:
            return words["missed"]
        case JobStatus.CANCELLED:
            return words["cancelled"]
        case _:
            return words["done"]
