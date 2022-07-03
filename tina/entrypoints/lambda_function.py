from datetime import datetime, date, timezone
import boto3

from tina.scheduler import ScheduleEntry, ScheduledAction

from ..scheduler import Scheduler

client = boto3.client("dynamodb")


def lambda_handler(event, context):
    scheduler = Scheduler()
    overdue_tasks = scheduler.get_overdue_tasks()
    output = [
        (entry.timeUtc.strftime("%Y/%m/%d %H:%M:%S"), entry.action.actionKey)
        for entry in overdue_tasks
    ]

    return {"statusCode": 200, "body": output}
