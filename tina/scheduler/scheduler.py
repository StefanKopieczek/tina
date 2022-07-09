import logging
from typing import Callable, List
from .persistence import SchedulePersistence
from .objects import ScheduleEntry, ScheduledAction
from datetime import datetime, timezone, timedelta


logger = logging.getLogger(__name__)


# Our schedule is bucketed by day, so we can't look back an unbounded period
# for tasks that are overdue. Since we should run and reschedule any overdue tasks
# fairly frequently, we don't need to go back too far.
OVERDUE_TASK_LOOKBACK_DAYS = 3


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
            logger.info("Executing due tasks: {}", tasks)
        else:
            logger.info("No tasks due")
        for task in tasks:
            self._invoke_action(task.action.actionKey)
            self.persistence.delete_schedule_entry(task)
        return len(tasks)

    def get_overdue_tasks(self) -> List[ScheduleEntry]:
        today = self.clock().date()
        days = [
            today - timedelta(days=offset)
            for offset in range(OVERDUE_TASK_LOOKBACK_DAYS + 1)
        ]
        day_buckets = [self.persistence.get_schedule_on_date(day) for day in days]
        tasks = [task for bucket in day_buckets for task in bucket]
        return sorted(tasks, key=lambda task: task.timeUtc)

    def do_with_delay(self, action_key: str, delay: timedelta) -> None:
        self.do_at_time(action_key, self.clock() + delay)

    def do_at_time(self, action_key: str, due_time: datetime) -> None:
        entry = ScheduleEntry(timeUtc=due_time, action=ScheduledAction(action_key))
        logger.info(f"Rescheduled {action_key} for {due_time}")
        self.persistence.put_schedule_entry(entry)

    def register_action(self, action_key: str, callback_fn: Callable[[], None]) -> None:
        self.callback_map[action_key] = callback_fn

    def _invoke_action(self, action_key: str) -> None:
        if action_key in self.callback_map:
            self.callback_map[action_key]()
        else:
            logger.error("Action '%s' fired, but no handler was registered", action_key)
