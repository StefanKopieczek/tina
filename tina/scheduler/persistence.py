from datetime import datetime, timezone
from typing import Dict, List
from .objects import ScheduleEntry, ScheduledAction
from boto3 import Session
from boto3.dynamodb.conditions import Key, Attr
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table


SCHEDULE_TABLE = "TinaSchedule"


class SchedulePersistence:
    def __init__(self):
        self.session = Session().resource("dynamodb")
        self.table = self.session.Table(SCHEDULE_TABLE)

    def get_due_entries(self, current_time: datetime = None) -> List[ScheduleEntry]:
        results = self.table.scan(
            FilterExpression=Key("ScheduledTime").lte(_epoch_time(current_time))
        )["Items"]
        return list(map(self._deserialize_entry, results))

    def get_entries_for_action(self, action_key: str) -> List[ScheduleEntry]:
        results = self.table.scan(FilterExpression=Attr("ActionKey").eq(action_key))[
            "Items"
        ]
        return list(map(self._deserialize_entry, results))

    def put_schedule_entry(self, entry: ScheduleEntry) -> None:
        self.table.put_item(Item=self._serialize_entry(entry))

    def delete_schedule_entry(self, entry: ScheduleEntry) -> None:
        self.table.delete_item(
            Key={
                "ScheduledTime": _epoch_time(entry.timeUtc),
                "ActionKey": entry.action.actionKey,
            }
        )

    @staticmethod
    def _serialize_entry(entry: ScheduleEntry) -> Dict[str, any]:
        return {
            "ScheduledTime": _epoch_time(entry.timeUtc),
            "ActionKey": entry.action.actionKey,
        }

    @staticmethod
    def _deserialize_entry(entry_item: Dict[str, any]) -> ScheduleEntry:
        return ScheduleEntry(
            timeUtc=_parse_epoch_time(entry_item["ScheduledTime"]),
            action=ScheduledAction(actionKey=entry_item["ActionKey"]),
        )


def _epoch_time(time: datetime):
    return int(time.timestamp())


def _parse_epoch_time(epoch_time: int):
    return datetime.fromtimestamp(epoch_time, timezone.utc)
