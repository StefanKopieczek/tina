import inflect
import re

from random import choice

from ..conversation import Conversation, ConversationTracker, state
from ..dialog import greeting, yesorno
from .persistence import Larder


number_regex = re.compile("[\d\.]+")


class StockCheck(Conversation):
    def __init__(self, conversation_tracker: ConversationTracker, recipient: str):
        super().__init__(conversation_tracker, recipient)

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
                    "Could you check on some things in the fridge/cupboards for me?",
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
        else:
            self.send("Sorry, I didn't quite get that. Try again?")

    def ask_next_question(self):
        larder = Larder()
        due_items = larder.get_items_due_update()
        if due_items:
            p = inflect.engine()
            item = next(iter(due_items))
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
        self.set_state("done")

    @state
    def done(self, _message, _data):
        self.send("No need to keep chatting to me - go do something fun!")
