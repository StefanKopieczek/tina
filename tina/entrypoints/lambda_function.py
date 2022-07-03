import datetime
import boto3
from ..scheduler import new_dynamodb_session, get_schedule_on_date

client = boto3.client("dynamodb")


def lambda_handler(event, context):
    dynamodb = new_dynamodb_session()

    return {
        "statusCode": 200,
        "body": get_schedule_on_date(dynamodb, datetime.date(2022, 1, 1)),
    }
