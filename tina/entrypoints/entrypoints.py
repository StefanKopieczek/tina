from ..conversation import ConversationTracker
from ..greeting import Greeting
from ..twilio import get_recipients
from urllib.parse import unquote


def check_in(event, context):
    for recipient in get_recipients():
        greeting = Greeting(ConversationTracker(), recipient)
        greeting.initiate()
    return {"statusCode": 200, "body": "Done!"}


def handle_message(event, context):
    sender = unquote(event["From"])
    body = unquote(event["Body"])
    conversations = ConversationTracker()
    conversations.handle_message(sender, body)
    return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
