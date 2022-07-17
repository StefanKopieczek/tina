from dataclasses import replace
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Tuple
from boto3 import Session
from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table


CONVERSATIONS_TABLE = "TinaConversation"


class ConversationsPersistence:
    def __init__(self):
        self.session = Session().resource("dynamodb")
        self.table = self.session.Table(CONVERSATIONS_TABLE)

    def get_current_conversation(self, recipient: str) -> Tuple[str, str, str]:
        item = self.table.get_item(Key={"Recipient": recipient})["Item"]
        return item["ConversationKey"], item["State"], item["Data"]

    def set_current_conversation(
        self, recipient: str, conversation_key: str, state: str, data: Dict[str, Any]
    ):
        self.table.put_item(
            Item={
                "Recipient": recipient,
                "ConversationKey": conversation_key,
                "State": state,
                "Data": data,
            }
        )

    def delete_current_conversation(self, recipient: str):
        self.table.delete_item(Key={"Recipient": recipient})
