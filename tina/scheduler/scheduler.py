import logging
from typing import Callable, List
from .persistence import SchedulePersistence
from .objects import ScheduleEntry, ScheduledAction
from datetime import datetime, timezone, timedelta


logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(
        self,
        persistence: SchedulePersistence = None,
        clock: Callable[[], datetime] = None,
    ):
        if not persistence:
            persistence = SchedulePersistence()
        self.persistence = persistence

        if not clock:
            clock = lambda: datetime.now(timezone.utc)
        self.clock = clock

        self.callback_map = {}

    def execute_all(self) -> int:
        tasks = self.get_overdue_tasks()
        if tasks:
            logger.info(f"Executing due tasks: {tasks}")
        else:
            logger.info("No tasks due")
        for task in tasks:
            self._invoke_action(task.action.actionKey)
            self.persistence.delete_schedule_entry(task)
        return len(tasks)

    def get_overdue_tasks(self) -> List[ScheduleEntry]:
        tasks = self.persistence.get_due_entries(current_time=self.clock())
        return sorted(tasks, key=lambda task: task.timeUtc)

    def do_with_delay(self, action_key: str, delay: timedelta) -> None:
        self.do_at_time(action_key, self.clock() + delay)

    def do_at_time(self, action_key: str, due_time: datetime) -> None:
        entry = ScheduleEntry(timeUtc=due_time, action=ScheduledAction(action_key))
        logger.info(f"Scheduled {action_key} for {due_time}")
        self.persistence.put_schedule_entry(entry)

    def ensure_scheduled(self, action_key) -> None:
        existing_entries = self.persistence.get_entries_for_action(action_key)
        if not existing_entries:
            logger.warn(f"Action {action_key} was not scheduled; will run immediately")
            self.do_at_time(action_key, self.clock())

    def register_action(self, action_key: str, callback_fn: Callable[[], None]) -> None:
        self.callback_map[action_key] = callback_fn

    def _invoke_action(self, action_key: str) -> None:
        if action_key in self.callback_map:
            self.callback_map[action_key]()
        else:
            logger.error("Action '%s' fired, but no handler was registered", action_key)
