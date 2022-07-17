from __future__ import annotations
from logging.handlers import MemoryHandler
import inflect
import inspect
import logging
from ..dialog import generic_reply
from ..twilio import send_sms
from .persistence import ConversationsPersistence
from typing import Any, Callable, Dict, List, Tuple, Type, TypeVar


logger = logging.getLogger(__name__)


class ConversationTypeRegistry:
    def __init__(self):
        self.type_map: dict[str, Type[Conversation]] = {}

    def register(self, conversation_type: Type[Conversation]) -> None:
        self.type_map[conversation_type.key] = conversation_type

    def get_conversation_handler(self, conversation_key: str) -> Type[Conversation]:
        return self.type_map[conversation_key]

    def get_all_types(self) -> List[Type[Conversation]]:
        return list(self.type_map.values())


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
        maybe_conversation = self.persistence.get_current_conversation(sender)

        if maybe_conversation is None:
            self.handle_spontaneous_message(sender, contents)
        else:
            conversation_key, state, data = maybe_conversation
            self.handle_conversation_message(
                conversation_key, state, data, sender, contents
            )

    def handle_spontaneous_message(self, sender, contents):
        for conversation_type in self.registry.get_all_types():
            try:
                conversation = conversation_type(self, sender)
                was_handled = conversation.handle_spontaneous_message(contents)
                if was_handled:
                    break
            except Exception as e:
                logger.exception("Exception when handling spontaneous message")
                continue
        else:
            send_sms(sender, generic_reply())

    def handle_conversation_message(
        self,
        conversation_key: str,
        state: str,
        data: Dict[str, any],
        sender: str,
        contents: str,
    ) -> None:
        try:
            conversation_type = self.registry.get_conversation_handler(conversation_key)
        except:
            logger.error(
                f"Unable to find handler for conversation '{conversation_key}'"
            )
            send_sms(
                sender,
                "Sorry, I completely lost track of what we were talking about. Never mind - it probably wasn't important!",
            )
            self.persistence.delete_current_conversation(conversation.recipient)

        try:
            conversation = conversation_type(self, sender)
            handler = getattr(conversation, state)
        except:
            logger.error(
                f"Unable to find handler for conversation state ({conversation_key},{state} - ending"
            )
            send_sms(
                conversation.recipient,
                "Sorry, I completely lost track of what we were talking about. Never mind - it probably wasn't important!",
            )
            self.persistence.delete_current_conversation(conversation.recipient)
            return

        try:
            handler(contents, data)
        except Exception as e:
            p = inflect.engine()
            send_sms(
                conversation.recipient,
                f"Gah, sorry, I hit {p.an(str(e.__class__))} while trying to reply to you. It's frustrating being a computer sometimes. Try again and let's see if I can get it right this time!",
            )
            raise e

    def set_current_conversation(
        self, recipient: str, key: str, state: str, data: dict[str, Any]
    ) -> None:
        self.persistence.set_current_conversation(recipient, key, state, data)

    def end_current_conversation(self, recipient: str) -> None:
        self.persistence.delete_current_conversation(recipient)


class ConversationMeta(type):
    def __new__(cls, name, bases, attrs):
        assert name == "Conversation" or any(
            Conversation in inspect.getmro(base) for base in bases
        ), "All conversations must subtype Conversation"
        states = {}
        new_request_handler = None
        for k, v in attrs.items():
            if inspect.isfunction(v):
                if getattr(k, "is_conversation_state", False):
                    states[k] = v
                if getattr(k, "is_new_request_handler", False):
                    assert (
                        new_request_handler is None
                    ), "Only one @new_request_handler annotation is allowed per Conversation!"
                    new_request_handler = v

        for base in bases:
            if hasattr(base, "_states"):
                states.update(base._states)
        attrs["_states"] = states

        conversation_type = type.__new__(cls, name, bases, attrs)
        conversation_type.key = (
            conversation_type.__module__ + "." + conversation_type.__qualname__
        )
        global_registry.register(conversation_type)

        if new_request_handler is not None:
            global_registry.register_for_user_initiation()

        return conversation_type


class Conversation(metaclass=ConversationMeta):
    """
    All Conversations should inherit from this base class.
    Conversations should have an __init__ that takes two arguments (other than 'self') - a ConversationTracker and a recipient string.
    It must call `super(tracker, recipient)`.
    Conversations should contain zero or more state methods, annotated as @state.
    Each state method should take two arguments - message contents (str) and data (dict from string keys to arbitrary values).

    When a conversation calls set_state, it is registering itself for a callback (in a future lambda call) when the recipient
    replies to the message. The Conversation will be reinitialized with the given recipient, and the corresponding state method
    will be called, passing the contents of the message and the stored data.

    Conversations can also register for callbacks on new messages, outside of conversations, that meet specified predicates.
    They do this by overriding handle_spontaneous_message, which is passed the contents of the message as a string.
    They should return True if the message was handled, and False otherwise, so that the caller knows whether to pass the
    message to other handlers.
    """

    def __init__(self, conversation_tracker: ConversationTracker, recipient: str):
        self.conversation_tracker = conversation_tracker
        self.recipient = recipient

    def set_state(self, new_state: str, data: dict[str, Any] = None):
        if data is None:
            data = {}
        assert hasattr(self, new_state)
        state_fn = getattr(self, new_state)
        assert inspect.ismethod(state_fn)
        assert state_fn.is_conversation_state  # i.e. is annotated with @state
        self.conversation_tracker.set_current_conversation(
            self.recipient, self.key, new_state, data
        )

    def end_conversation(self):
        self.conversation_tracker.end_current_conversation(self.recipient)

    def send(self, message):
        send_sms(self.recipient, message)

    def handle_spontaneous_message(self, contents) -> bool:
        return False


def state(fn):
    fn.is_conversation_state = True
    return fn
