from tina.conversation.conversation import ConversationTracker
import random
import re
import requests
from ..conversation import Conversation, state


class Joker(Conversation):
    def __init__(self, tracker: ConversationTracker, recipient: str):
        super().__init__(tracker, recipient)
        self.recipient = recipient

    def handle_spontaneous_message(self, contents) -> bool:
        contents = contents.lower()
        words = re.findall(r"[a-z'-]+", contents)
        if "joke" in words:
            self.tell_joke()
            return True
        elif "knock knock" in contents:
            self.send("Who's there?")
            self.set_state("be_told_who_is_there")
            return True
        elif "ha" in words or "ha-ha" in words or "haha" in words or "funny" in words:
            self.send("I'm a laugh a minute!")
            return True

        print(contents)
        return False

    def tell_joke(self):
        r = requests.get(
            "https://icanhazdadjoke.com/", headers={"Accept": "application/json"}
        )
        self.send(r.json()["joke"])

    @state
    def be_told_who_is_there(self, contents, _data):
        subject = contents[:1].upper() + contents[1:]
        self.send(subject + " who?")
        self.set_state("respond_appropriately")

    @state
    def respond_appropriately(self, contents, _data):
        self.send(
            random.choice(
                [
                    "Hilarious.",
                    "Don't give up the day job...",
                    "Ha. Ha.",
                    "Side-splitting...",
                ]
            )
        )
        self.end_conversation()
