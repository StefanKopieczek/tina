from ..conversation import ConversationTracker
from ..larder import StockCheck
from ..twilio import get_recipients
from urllib.parse import unquote


def check_in(event, context):
    for recipient in get_recipients():
        stock_check = StockCheck(ConversationTracker(), recipient)
        if stock_check.should_initiate:
            stock_check.initiate()
    return {"statusCode": 200, "body": "Done!"}


def handle_message(event, context):
    sender = unquote(event["From"])
    body = unquote(event["Body"])
    conversations = ConversationTracker()
    conversations.handle_message(sender, body)
    return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
