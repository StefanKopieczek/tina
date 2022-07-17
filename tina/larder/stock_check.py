from datetime import timedelta
import inflect
import logging
import re
import random

from random import choice

from ..conversation import Conversation, ConversationTracker, state
from ..dialog import greeting, yesorno
from .persistence import Larder
from ..scheduler import Scheduler
from ..twilio import get_recipients


logger = logging.getLogger(__name__)
number_regex = re.compile("[\d\.]+")


def maybe_check_stock():
    for recipient in get_recipients():
        stock_check = StockCheck(ConversationTracker(), recipient)
        if stock_check.should_initiate():
            logging.info("Stock check needed for one or more items - initiating")
            stock_check.initiate()
        else:
            logging.info("Stock is up to date - will not request stock check")
            stock_check.reschedule()


class StockCheck(Conversation):
    ACTION_KEY = "StockCheck"

    def __init__(
        self,
        conversation_tracker: ConversationTracker,
        recipient: str,
        scheduler: Scheduler = None,
    ):
        super().__init__(conversation_tracker, recipient)
        if scheduler is None:
            scheduler = Scheduler()
        self.scheduler = scheduler

    def should_initiate(self):
        larder = Larder()
        return larder.get_items_due_update()

    def initiate(self):
        message = (
            greeting()
            + " "
            + choice(
                [
                    "Is now a good time for a quick stock check?",
                    "Mind checking the larder for me?",
                    "I just wanted to check if you're running out of anything. Is now a good time?",
                    "Could you check on some things in the fridge and cupboards for me?",
                ]
            )
        )
        self.send(message)
        self.set_state("get_user_goahead")

    @state
    def get_user_goahead(self, message, _data):
        user_preference = yesorno(message)
        if user_preference == "yes":
            self.send("Great, let's get started.")
            self.ask_next_question()
        elif user_preference == "no":
            self.send("That's ok! Another time then.")
            self.reschedule()
        else:
            self.send("Sorry, I didn't quite get that. Try again?")

    def ask_next_question(self):
        larder = Larder()
        due_items = larder.get_items_due_update()
        if due_items:
            p = inflect.engine()
            item = next(iter(due_items))
            if item.groupNoun is not None:
                self.send(
                    f"How many {p.plural(item.groupNoun)} of {item.name} do you have?"
                )
            else:
                self.send(f"How many {p.plural(item.name)} do you have?")
            self.set_state("interpret_count", {"current_item": item.name})
        else:
            self.finish()

    @state
    def interpret_count(self, message, data):
        current_item = data["current_item"]
        count_match = number_regex.search(message)
        if count_match:
            quantity = float(count_match.group(0))
            larder = Larder()
            larder.update_quantity(current_item, quantity)
            self.ask_next_question()
        else:
            self.send(
                "Sorry, didn't catch that. I don't understand number words, yet, so can you use digits?"
            )

    def finish(self):
        self.send(
            choice(
                [
                    "OK, that's everything. Thank you!",
                    "Thanks a lot - that's all I needed.",
                    "And that's a wrap. Thanks for your help!",
                    "OK sweet - that's all I needed right now. Have a good day!",
                    "Thanks, my records are now up to date. Have a great rest of your day!",
                ]
            )
        )
        self.end_conversation()
        self.reschedule()

    def reschedule(self, mean_hours=24):
        delay = random.randint(int(mean_hours * 0.5), int(mean_hours * 1.5))
        self.scheduler.do_with_delay(self.ACTION_KEY, timedelta(hours=delay))
