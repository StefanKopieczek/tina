import datetime
from .objects import ScheduleEntry
from boto3 import Session
from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table


SCHEDULE_TABLE = "TinaSchedule"


def new_dynamodb_session() -> DynamoDBServiceResource:
    return Session().resource("dynamodb")


def get_schedule_on_date(
    dynamodb: DynamoDBServiceResource, date: datetime.date
) -> list[ScheduleEntry]:
    schedule_table = dynamodb.Table(SCHEDULE_TABLE)
    partition_key = _get_epoch_day_for_date(date)
    return schedule_table.query(
        KeyConditionExpression=Key("EpochDay").eq(partition_key)
    )


def _get_epoch_day_for_date(date: datetime.date) -> int:
    return (date - datetime.date(1970, 1, 1)).days
