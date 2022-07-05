from ..conversation import ConversationTracker
from ..larder import StockCheck, maybe_check_stock
from ..scheduler import Scheduler
from ..twilio import get_recipients
from urllib.parse import unquote


def check_in(event, context):
    scheduler = Scheduler()
    scheduler.register_action(StockCheck.ACTION_KEY, maybe_check_stock)
    scheduler.execute_all()
    return {"statusCode": 200, "body": "Done!"}


def handle_message(event, context):
    sender = unquote(event["From"])
    body = unquote(event["Body"])
    conversations = ConversationTracker()
    conversations.handle_message(sender, body)
    return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'