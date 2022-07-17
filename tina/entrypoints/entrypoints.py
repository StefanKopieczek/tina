import logging
from ..bagatelles import register_bagatelles
from ..conversation import ConversationTracker
from ..larder import StockCheck, maybe_check_stock
from ..playwright import test_playwright
from ..shopper.ocado import main
from ..scheduler import Scheduler
from urllib.parse import unquote


logging.getLogger("tina").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


ALL_ACTIONS = [
    (StockCheck.ACTION_KEY, maybe_check_stock),
]


def check_in(event, context):
    logger.info("Running scheduled check-in")
    scheduler = Scheduler()

    for action_key, handler in ALL_ACTIONS:
        scheduler.register_action(action_key, handler)
        scheduler.ensure_scheduled(action_key)

    scheduler.execute_all()
    return {"statusCode": 200, "body": "Done!"}


def handle_message(event, context):
    register_bagatelles()
    sender = unquote(event["From"])
    body = unquote(event["Body"]).replace("+", " ")
    logger.info("Handling a message from " + sender)
    conversations = ConversationTracker()
    conversations.handle_message(sender, body)
    return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'


def ping(event, context):
    return {"statusCode": 200, "body": "Done!"}


def manual(event, context):
    # Used for manual testing of new functions and workflows, by
    # editing the code below.
    main()
    return {"statusCode": 200, "body": "Done!"}
