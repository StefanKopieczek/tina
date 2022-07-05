from __future__ import annotations
import inspect
from ..twilio import send_sms
from .persistence import ConversationsPersistence
from typing import Any, Type, TypeVar


class ConversationTypeRegistry:
    def __init__(self):
        self.type_map: dict[str, Type[Conversation]] = {}

    def register(self, conversation_type: Type[Conversation]) -> None:
        self.type_map[conversation_type.key] = conversation_type

    def lookup(self, conversation_key: str) -> Type[Conversation]:
        return self.type_map[conversation_key]


global_registry = ConversationTypeRegistry()


def get_conversation_registry():
    return global_registry


class ConversationTracker:
    def __init__(self, persistence=None, registry=global_registry):
        if not persistence:
            persistence = ConversationsPersistence()
        self.persistence = persistence
        self.registry = registry

    def handle_message(self, sender: str, contents: str) -> None:
        conversation_key, state, data = self.persistence.get_current_conversation(
            sender
        )
        conversation_type = self.registry.lookup(conversation_key)
        conversation = conversation_type(self, sender)
        getattr(conversation, state)(contents, data)

    def set_current_conversation(
        self, recipient: str, key: str, state: str, data: dict[str, Any]
    ):
        self.persistence.set_current_conversation(recipient, key, state, data)


class ConversationMeta(type):
    def __new__(cls, name, bases, attrs):
        assert name == "Conversation" or any(
            Conversation in inspect.getmro(base) for base in bases
        ), "All conversations must subtype Conversation"
        states = {}
        for k, v in attrs.items():
            if inspect.isfunction(v) and getattr(k, "is_conversation_state", False):
                states[k] = v
        for base in bases:
            if hasattr(base, "_states"):
                states.update(base._states)
        attrs["_states"] = states

        conversation_type = type.__new__(cls, name, bases, attrs)
        conversation_type.key = (
            conversation_type.__module__ + "." + conversation_type.__qualname__
        )
        global_registry.register(conversation_type)
        return conversation_type


class Conversation(metaclass=ConversationMeta):
    """
    All Conversations should inherit from this base class.
    Conversations should have an __init__ that takes two arguments - a ConversationTracker and a recipient string.
    It must call `super(tracker, recipient)`.
    Conversations should contain one or more state methods, annotated as @state.
    Each state method should take two arguments - message contents (str) and data (dict from string keys to arbitrary values).

    When a conversation calls set_state, it is registering itself for a callback (in a future lambda call) when the recipient
    replies to the message. The Conversation will be reinitialized with the given recipient, and the corresponding state method
    will be called, passing the contents of the message and the stored data.
    """

    def __init__(self, conversation_tracker: ConversationTracker, recipient: str):
        self.conversation_tracker = conversation_tracker
        self.recipient = recipient

    def set_state(self, new_state: str, data: dict[str, Any] = None):
        if data is None:
            data = {}
        assert hasattr(self, new_state)
        state_fn = getattr(self, new_state)
        print(state_fn)
        assert inspect.ismethod(state_fn)
        assert state_fn.is_conversation_state  # i.e. is annotated with @state
        self.conversation_tracker.set_current_conversation(
            self.recipient, self.key, new_state, data
        )

    def send(self, message):
        send_sms(self.recipient, message)


def state(fn):
    fn.is_conversation_state = True
    return fn