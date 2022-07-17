from __future__ import annotations
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List
import unittest
from unittest.mock import MagicMock

from tina.larder.objects import LarderItem, ShopOption
from .persistence import Larder
from ..utils import parse_epoch_time, to_epoch_time


class TestReads(unittest.TestCase):
    def test_get_single_item(self):
        session = MockTable(
            self,
            [{"ItemName": "banana", "LastChecked": 1658062168, "Quantity": Decimal(3)}],
        ).as_session()
        larder = Larder(session=session)
        bananas = larder.get_item("banana")
        self.assertEqual(
            bananas,
            LarderItem(
                name="banana", lastChecked=parse_epoch_time(1658062168), quantity=3
            ),
        )

    def test_item_with_group_noun(self):
        session = MockTable(
            self,
            [
                {
                    "ItemName": "tuna",
                    "LastChecked": 1658062168,
                    "Quantity": Decimal(2),
                    "GroupNoun": "tin",
                }
            ],
        ).as_session()
        larder = Larder(session=session)
        tuna = larder.get_item("tuna")
        self.assertEqual("tin", tuna.groupNoun)

    def test_item_with_check_frequency(self):
        session = MockTable(
            self,
            [
                {
                    "ItemName": "tuna",
                    "LastChecked": 1658062168,
                    "Quantity": Decimal(2),
                    "CheckFrequencyInDays": 7,
                }
            ],
        ).as_session()
        larder = Larder(session=session)
        tuna = larder.get_item("tuna")
        self.assertEqual(7, tuna.checkFrequencyDays)

    def test_item_with_shopping_details(self):
        session = MockTable(
            self,
            [
                {
                    "ItemName": "tuna",
                    "LastChecked": 1658062168,
                    "Quantity": Decimal(2),
                    "BuyVia": "fakemart",
                    "TargetAmount": Decimal(6),
                    "OnlineShopOptions": [
                        {"ProductId": "fancy-tin-multipack", "Quantity": Decimal(3)},
                        {"ProductId": "fancy-tin-single", "Quantity": Decimal(1)},
                        {"ProductId": "super-saver-tuna", "Quantity": Decimal(1)},
                    ],
                }
            ],
        ).as_session()
        larder = Larder(session=session)
        tuna = larder.get_item("tuna")
        self.assertEqual("fakemart", tuna.buyVia)
        self.assertEqual(6, tuna.targetAmount),
        self.assertListEqual(
            [
                ShopOption("fancy-tin-multipack", 3),
                ShopOption("fancy-tin-single", 1),
                ShopOption("super-saver-tuna", 1),
            ],
            tuna.onlineShopOptions,
        )

    def test_missing_quantity_rejected(self):
        session = MockTable(
            self,
            [
                {
                    "ItemName": "tuna",
                    "LastChecked": 1658062168,
                }
            ],
        ).as_session()
        larder = Larder(session=session)
        self.assertRaises(KeyError, larder.get_item, "tuna")

    def test_missing_check_time_rejected(self):
        session = MockTable(
            self,
            [
                {
                    "ItemName": "tuna",
                    "Quantity": Decimal(1),
                }
            ],
        ).as_session()
        larder = Larder(session=session)
        self.assertRaises(KeyError, larder.get_item, "tuna")

    def test_missing_shop_options_fail_when_buy_via_present(self):
        session = MockTable(
            self,
            [
                {
                    "ItemName": "tuna",
                    "LastChecked": 1658062168,
                    "Quantity": Decimal(2),
                    "BuyVia": "fakemart",
                    "TargetAmount": Decimal(6),
                }
            ],
        ).as_session()
        larder = Larder(session=session)
        self.assertRaises(KeyError, larder.get_item, "tuna")

    def test_empty_shop_options_fail(self):
        session = MockTable(
            self,
            [
                {
                    "ItemName": "tuna",
                    "LastChecked": 1658062168,
                    "Quantity": Decimal(2),
                    "BuyVia": "fakemart",
                    "TargetAmount": Decimal(6),
                    "OnlineShopOptions": [],
                }
            ],
        ).as_session()
        larder = Larder(session=session)
        self.assertRaises(ValueError, larder.get_item, "tuna")

    def test_missing_target_amount_allowed_when_buy_via_present(self):
        session = MockTable(
            self,
            [
                {
                    "ItemName": "tuna",
                    "LastChecked": 1658062168,
                    "Quantity": Decimal(2),
                    "BuyVia": "fakemart",
                    "OnlineShopOptions": [
                        {"ProductId": "super-saver-tuna", "Quantity": 1},
                    ],
                }
            ],
        ).as_session()
        larder = Larder(session=session)
        try:
            larder.get_item("tuna")
        except KeyError:
            self.fail(
                "Leaving out the TargetAmount should be valid, but threw KeyError"
            )

    def test_get_contents(self):
        session = MockTable(
            self,
            [
                {"ItemName": "banana", "LastChecked": 1658062168, "Quantity": 3},
                {
                    "ItemName": "tuna",
                    "LastChecked": 1658062168,
                    "Quantity": Decimal(2),
                    "GroupNoun": "tin",
                },
            ],
        ).as_session()
        larder = Larder(session=session)
        self.assertCountEqual(
            [
                LarderItem(
                    name="banana", lastChecked=parse_epoch_time(1658062168), quantity=3
                ),
                LarderItem(
                    name="tuna",
                    lastChecked=parse_epoch_time(1658062168),
                    quantity=Decimal(2),
                    groupNoun="tin",
                ),
            ],
            larder.get_contents(),
        )

    def test_scan_performs_validation(self):
        session = MockTable(
            self,
            [
                {"ItemName": "invalidentry"},
                {
                    "ItemName": "banana",
                    "LastChecked": 1658062168,
                    "Quantity": Decimal(3),
                },
            ],
        ).as_session()
        larder = Larder(session=session)
        self.assertRaises(KeyError, larder.get_contents)


class TestWrites(unittest.TestCase):
    def test_putting_minimal_item(self):
        table = MockTable(self)
        larder = Larder(session=table.as_session())
        larder.put_item(
            LarderItem(
                name="banana", lastChecked=parse_epoch_time(1658062168), quantity=3
            )
        )
        self.assertCountEqual(
            [{"ItemName": "banana", "LastChecked": 1658062168, "Quantity": Decimal(3)}],
            table._get_entries(),
        )

    def test_putting_maximal_item(self):
        table = MockTable(self)
        larder = Larder(session=table.as_session())
        larder.put_item(
            LarderItem(
                name="tuna",
                lastChecked=parse_epoch_time(1658062168),
                quantity=2,
                checkFrequencyDays=7,
                buyVia="fakemart",
                minAmount=2,
                targetAmount=6,
                onlineShopOptions=[
                    ShopOption("fancy-tin-multipack", 3),
                    ShopOption("fancy-tin-single", 1),
                    ShopOption("super-saver-tuna", 1),
                ],
            )
        )
        self.assertCountEqual(
            [
                {
                    "ItemName": "tuna",
                    "LastChecked": 1658062168,
                    "Quantity": Decimal(2),
                    "CheckFrequencyInDays": 7,
                    "BuyVia": "fakemart",
                    "MinAmount": Decimal(2),
                    "TargetAmount": Decimal(6),
                    "OnlineShopOptions": [
                        {"ProductId": "fancy-tin-multipack", "Quantity": Decimal(3)},
                        {"ProductId": "fancy-tin-single", "Quantity": Decimal(1)},
                        {"ProductId": "super-saver-tuna", "Quantity": Decimal(1)},
                    ],
                }
            ],
            table._get_entries(),
        )

    def test_validate_on_write(self):
        larder = Larder(session=MockTable(self).as_session())
        self.assertRaises(
            KeyError,
            larder.put_item,
            LarderItem(
                name="Item missing shop options",
                lastChecked=parse_epoch_time(1688062168),
                quantity=1,
                buyVia="fakemart",
            ),
        )

    def test_update_quantity(self):
        table = MockTable(
            self,
            [{"ItemName": "banana", "LastChecked": 1658062168, "Quantity": Decimal(3)}],
        )
        larder = Larder(session=table.as_session())
        larder.update_quantity("banana", 17)
        self.assertEqual(17, table.contents["banana"]["Quantity"])


class TestOverdueRetrieval(unittest.TestCase):
    def test_get_overdue_items(self):
        now = datetime(
            year=2022,
            month=7,
            day=3,
            hour=18,
            minute=30,
            second=00,
            tzinfo=timezone.utc,
        )

        table = MockTable(
            self,
            [
                {
                    "ItemName": "shouldn't ever check",
                    "LastChecked": to_epoch_time(now),
                    "Quantity": Decimal(3),
                },
                {
                    "ItemName": "not due",
                    "LastChecked": to_epoch_time(now - timedelta(days=2)),
                    "Quantity": Decimal(2),
                    "CheckFrequencyInDays": 7,
                },
                {
                    "ItemName": "due",
                    "LastChecked": to_epoch_time(now - timedelta(days=15)),
                    "Quantity": Decimal(1),
                    "CheckFrequencyInDays": 14,
                },
            ],
        )

        larder = Larder(clock=lambda: now, session=table.as_session())
        self.assertCountEqual(
            [
                LarderItem(
                    name="due",
                    lastChecked=now - timedelta(days=15),
                    quantity=1,
                    checkFrequencyDays=14,
                )
            ],
            larder.get_items_due_update(),
        )


TableEntry = Dict[str, Any]


class MockTable:
    def __init__(self, test: unittest.TestCase, entries: List[TableEntry] = None):
        if entries is None:
            entries = []
        self.test = test
        self.contents = MockTable.group_by_item_id(entries)

    def scan(self) -> List[TableEntry]:
        return {"Items": self.contents.values()}

    def get_item(self, Key: Dict[str, Any]) -> Dict[str, TableEntry]:
        self.test.assertCountEqual(Key.keys(), ["ItemName"], msg="Unexpected query key")
        return {"Item": self.contents[Key["ItemName"]]}

    def put_item(self, Item: TableEntry) -> None:
        self.test.assertIn("ItemName", Item, msg=f"Missing item name on item '{Item}'")
        self.contents[Item["ItemName"]] = Item

    def as_session(self):
        """
        Returns an object that mimics a boto3 Session, so a consumer can call
        session.resource("dynamodb").table("Larder") and get this MockTable back.
        """

        def table_getter(table_name):
            self.test.assertEqual("Larder", table_name)
            return self

        session = MagicMock()
        session.resource.return_value.Table.side_effect = table_getter
        return session

    def _get_entries(self):
        return self.contents.values()

    @staticmethod
    def group_by_item_id(items: List[TableEntry]) -> Dict[str, TableEntry]:
        results = {}
        for item in items:
            assert (
                "ItemName" in item
            ), f"Test error - missing item name when constructing table ({item})"
            assert (
                item["ItemName"] not in results
            ), f"Test error - duplicate key '{item['ItemName']}' when constructing table"
            results[item["ItemName"]] = item
        return results
