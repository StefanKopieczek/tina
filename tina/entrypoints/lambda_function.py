from datetime import datetime, date, timezone
import boto3

from tina.scheduler import ScheduleEntry, ScheduledAction

from ..scheduler import SchedulePersistence

client = boto3.client("dynamodb")


def lambda_handler(event, context):
    persistence = SchedulePersistence()
    entries = persistence.get_schedule_on_date(date(2022, 7, 3))
    output = [
        (entry.timeUtc.strftime("%Y/%m/%d %H:%M:%S"), entry.action.actionKey)
        for entry in entries
    ]

    return {"statusCode": 200, "body": output}
