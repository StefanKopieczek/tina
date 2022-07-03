from datetime import datetime, date, timezone
import boto3

from tina.larder.objects import LarderItem

from ..larder import Larder

client = boto3.client("dynamodb")


def lambda_handler(event, context):
    larder = Larder()
    items = Larder().get_items_due_update()
    return {"statusCode": 200, "body": "\n".join(str(item) for item in items)}
