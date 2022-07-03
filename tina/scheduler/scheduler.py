from typing import Callable
from .persistence import SchedulePersistence
from .objects import ScheduleEntry
from datetime import datetime, timezone, timedelta


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

    def get_overdue_tasks(self) -> list[ScheduleEntry]:
        today = self.clock().date()
        days = [
            today - timedelta(days=offset)
            for offset in range(OVERDUE_TASK_LOOKBACK_DAYS + 1)
        ]
        day_buckets = [self.persistence.get_schedule_on_date(day) for day in days]
        tasks = [task for bucket in day_buckets for task in bucket]
        return sorted(tasks, key=lambda task: task.timeUtc)
