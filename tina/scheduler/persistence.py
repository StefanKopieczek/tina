from datetime import date, datetime, timezone
from typing import Dict
from .objects import ScheduleEntry, ScheduledAction
from boto3 import Session
from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table


SCHEDULE_TABLE = "TinaSchedule"


class SchedulePersistence:
    def __init__(self):
        self.session = Session().resource("dynamodb")
        self.table = self.session.Table(SCHEDULE_TABLE)

    def get_schedule_on_date(self, theDate: date) -> list[ScheduleEntry]:
        partition_key = _get_epoch_day_for_date(theDate)
        results = self.table.query(
            KeyConditionExpression=Key("EpochDay").eq(partition_key)
        )["Items"]
        return [self._deserialize_entry(result) for result in results]

    def put_schedule_entry(self, entry: ScheduleEntry) -> None:
        self.table.put_item(Item=self._serialize_entry(entry))

    @staticmethod
    def _serialize_entry(entry: ScheduleEntry) -> dict[str, any]:
        return {
            "EpochDay": _get_epoch_day_for_date(entry.timeUtc.date()),
            "EpochTime": int(entry.timeUtc.timestamp()),
            "ActionKey": entry.action.actionKey,
        }

    @staticmethod
    def _deserialize_entry(entry_item: dict[str, any]) -> ScheduleEntry:
        return ScheduleEntry(
            timeUtc=datetime.fromtimestamp(entry_item["EpochTime"], timezone.utc),
            action=ScheduledAction(actionKey=entry_item["ActionKey"]),
        )


def _get_epoch_day_for_date(theDate: date) -> int:
    return int((theDate - date(1970, 1, 1)).days)
