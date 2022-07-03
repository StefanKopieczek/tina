from datetime import datetime, date, timezone
import boto3

from tina.larder.objects import LarderItem

from ..larder import Larder
from ..twilio import notify

client = boto3.client("dynamodb")


def lambda_handler(event, context):
    larder = Larder()
    items = larder.get_items_due_update()
    notify("\n".join(str(item) for item in items))
    return {"statusCode": 200, "body": "Done!"}
