from dataclasses import replace
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List
from .objects import LarderItem
from boto3 import Session
from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table


LARDER_TABLE = "Larder"


class Larder:
    def __init__(self, clock=None):
        self.session = Session().resource("dynamodb")
        self.table = self.session.Table(LARDER_TABLE)
        if not clock:
            clock = lambda: datetime.now(timezone.utc)
        self.clock = clock

    def get_contents(self) -> List[LarderItem]:
        results = self.table.scan()["Items"]
        return [self._deserialize_entry(item) for item in results]

    def get_item(self, item_name: str) -> LarderItem:
        result = self.table.get_item(Key={"ItemName": item_name})
        return self._deserialize_entry(result["Item"])

    def put_item(self, item: LarderItem) -> None:
        self.table.put_item(Item=self._serialize_entry(item))

    def update_quantity(self, item_name: str, new_quantity: float) -> None:
        old_item = self.get_item(item_name)
        updated_item = replace(
            old_item, quantity=new_quantity, lastChecked=self.clock()
        )
        self.put_item(updated_item)

    def get_items_due_update(self):
        now = self.clock()
        return [
            item
            for item in self.get_contents()
            if item.lastChecked + timedelta(days=int(item.checkFrequencyDays)) < now
        ]

    @staticmethod
    def _deserialize_entry(entry_item: Dict[str, any]) -> LarderItem:
        return LarderItem(
            name=entry_item["ItemName"],
            checkFrequencyDays=entry_item["CheckFrequencyInDays"],
            lastChecked=datetime.fromtimestamp(entry_item["LastChecked"], timezone.utc),
            quantity=float(entry_item["Quantity"]),
            replaceAt=entry_item["ReplaceAt"],
        )

    @staticmethod
    def _serialize_entry(entry: LarderItem) -> Dict[str, any]:
        return {
            "ItemName": entry.name,
            "CheckFrequencyInDays": entry.checkFrequencyDays,
            "LastChecked": int(entry.lastChecked.timestamp()),
            "Quantity": Decimal(str(entry.quantity)),
            "ReplaceAt": entry.replaceAt,
        }
