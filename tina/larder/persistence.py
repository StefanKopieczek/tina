import boto3
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Callable, Dict, List, Optional

from tina.utils.dateutils import to_epoch_time
from .objects import LarderItem, ShopOption
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table


LARDER_TABLE = "Larder"


class Larder:
    def __init__(
        self, clock: Callable[[], datetime] = None, session: boto3.Session = None
    ):
        if not clock:
            clock = lambda: datetime.now(timezone.utc)
        if session is None:
            session = boto3.Session()
        self.clock = clock
        self.table = session.resource("dynamodb").Table(LARDER_TABLE)

    def get_contents(self) -> List[LarderItem]:
        results = self.table.scan()["Items"]
        return [self._deserialize_entry(item) for item in results]

    def get_item(self, item_name: str) -> LarderItem:
        result = self.table.get_item(Key={"ItemName": item_name})
        return self._deserialize_entry(result["Item"])

    def put_item(self, item: LarderItem) -> None:
        item.validate()
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
            if item.checkFrequencyDays is not None
            and item.lastChecked + timedelta(days=int(item.checkFrequencyDays)) < now
        ]

    @staticmethod
    def _deserialize_entry(entry_item: Dict[str, any]) -> LarderItem:
        item = LarderItem(
            name=entry_item["ItemName"],
            lastChecked=datetime.fromtimestamp(entry_item["LastChecked"], timezone.utc),
            quantity=entry_item["Quantity"],
            groupNoun=entry_item.get("GroupNoun"),
            checkFrequencyDays=entry_item.get("CheckFrequencyInDays"),
            minAmount=entry_item.get("MinAmount"),
            buyVia=entry_item.get("BuyVia"),
            targetAmount=entry_item.get("TargetAmount"),
            onlineShopOptions=Larder._deserialize_shop_options(
                entry_item.get("OnlineShopOptions")
            ),
        )
        item.validate()
        return item

    @staticmethod
    def _deserialize_shop_options(
        shop_options: Optional[List[Dict[str, any]]]
    ) -> Optional[List[ShopOption]]:
        if shop_options is None:
            return None

        results: List[ShopOption] = []
        for option in shop_options:
            results.append(
                ShopOption(productId=option["ProductId"], quantity=option["Quantity"])
            )
        return results

    @staticmethod
    def _serialize_entry(item: LarderItem) -> Dict[str, any]:
        entry = {
            "ItemName": item.name,
            "LastChecked": to_epoch_time(item.lastChecked),
            "Quantity": Decimal(str(item.quantity)),
        }

        if item.groupNoun is not None:
            entry["GroupNoun"] = item.groupNoun
        if item.checkFrequencyDays is not None:
            entry["CheckFrequencyInDays"] = item.checkFrequencyDays
        if item.minAmount is not None:
            entry["MinAmount"] = item.minAmount
        if item.buyVia is not None:
            entry["BuyVia"] = item.buyVia
        if item.targetAmount is not None:
            entry["TargetAmount"] = item.targetAmount
        if item.onlineShopOptions is not None:
            entry["OnlineShopOptions"] = [
                {
                    "ProductId": option.productId,
                    "Quantity": Decimal(str(option.quantity)),
                }
                for option in item.onlineShopOptions
            ]

        return entry
