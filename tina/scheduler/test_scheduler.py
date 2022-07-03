from __future__ import annotations
import typing
import unittest
from datetime import date, datetime, timezone
from .scheduler import Scheduler
from .objects import ScheduleEntry, ScheduledAction
from .persistence import SchedulePersistence
from tina.scheduler import persistence


TEST_TIME = datetime(
    year=2022, month=7, day=3, hour=18, minute=30, second=00, tzinfo=timezone.utc
)
NOW = lambda: TEST_TIME
TEST_DATE_FORMAT = "%Y/%m/%d %H:%M:%S"


class TestTaskRetrieval(unittest.TestCase):
    def test_no_overdue_tasks_when_db_empty(self):
        scheduler = Scheduler(MockPersistence().cast())
        self.assertFalse(len(scheduler.get_overdue_tasks()))

    def test_one_overdue_task(self):
        tasks = {"2022/07/03 01:00:00": "Example"}
        persistence = MockPersistence.with_tasks(tasks)
        scheduler = Scheduler(persistence, NOW)
        actual = scheduler.get_overdue_tasks()
        expected = MockPersistence.parse_action_descriptors(tasks)
        self.assertEqual(expected, actual)

    def test_not_all_tasks_due(self):
        tasks = {
            "2022/07/03 18:25:00": "This task is due",
            "2022/07/04 18:31:00": "This task is not",
        }
        persistence = MockPersistence.with_tasks(tasks)
        scheduler = Scheduler(persistence, NOW)
        actual = scheduler.get_overdue_tasks()
        expected = [
            MockPersistence.parse_action_descriptor(
                (
                    "2022/07/03 18:25:00",
                    "This task is due",
                )
            )
        ]
        self.assertEqual(expected, actual)

    def test_yesterday_due_tasks(self):
        tasks = {"2022/07/02 01:00:00": "Example"}
        persistence = MockPersistence.with_tasks(tasks)
        scheduler = Scheduler(persistence, NOW)
        actual = scheduler.get_overdue_tasks()
        expected = MockPersistence.parse_action_descriptors(tasks)
        self.assertEqual(expected, actual)


class MockPersistence:
    def __init__(self, tasks=None):
        if tasks is None:
            tasks = []
        self.tasks: list[ScheduleEntry] = tasks

    @classmethod
    def with_tasks(clazz, descriptors: map[str, str]) -> MockPersistence:
        return clazz(MockPersistence.parse_action_descriptors(descriptors))

    def get_schedule_on_date(self, theDate: date) -> list[ScheduleEntry]:
        return [task for task in self.tasks if task.timeUtc.date() == theDate]

    def put_schedule_entry(self, entry: ScheduleEntry):
        self.tasks.append(entry)

    def cast(self) -> SchedulePersistence:
        return typing.cast(SchedulePersistence, self)

    @staticmethod
    def parse_action_descriptor(descriptor):
        date_time = datetime.strptime(descriptor[0], TEST_DATE_FORMAT).replace(
            tzinfo=timezone.utc
        )

        return ScheduleEntry(timeUtc=date_time, action=ScheduledAction(descriptor[1]))

    @staticmethod
    def parse_action_descriptors(descriptors):
        return sorted(
            [
                MockPersistence.parse_action_descriptor(descriptor)
                for descriptor in descriptors.items()
            ],
            key=lambda e: e.timeUtc,
        )
