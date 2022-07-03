from datetime import datetime, date, timezone
import boto3

from tina.scheduler import ScheduleEntry, ScheduledAction

from ..scheduler import Scheduler

client = boto3.client("dynamodb")


def lambda_handler(event, context):
    executed_count = Scheduler().execute_all()

    return {"statusCode": 200, "body": f"Executed {executed_count} tasks"}
