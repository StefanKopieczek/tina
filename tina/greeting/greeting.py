import re
from ..conversation import Conversation, ConversationTracker, state


BAD = re.compile(r"[nN]ot .*(?:good|great)")


class Greeting(Conversation):
    def __init__(self, conversation_tracker: ConversationTracker, recipient: str):
        super().__init__(conversation_tracker, recipient)

    def initiate(self):
        self.send("Hi! How are you today?")
        self.set_state("respond", {})

    @state
    def respond(self, reply, _data):
        if BAD.search(reply) is not None:
            self.send("Oh, I'm sorry to hear that :(")
        elif "good" in reply.lower() or "great" in reply.lower():
            self.send("That's great to hear!")
        else:
            self.send("Thanks for sharing!")
        self.set_state("done", {})

    @state
    def done(self, reply, _data):
        self.send("Have a great day!")
