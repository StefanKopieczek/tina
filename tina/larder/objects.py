from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class LarderItem:
    name: str  # Primary key + human readable name of item (e.g. 'banana')
    lastChecked: datetime
    quantity: float  # How many we have as of the last check
    groupNoun: Optional[str] = None  # Tin, carton, bottle, jar, ...
    checkFrequencyDays: Optional[int] = None
    minAmount: Optional[float] = None  # Buy if fewer than this
    targetAmount: Optional[float] = None  # Buy back to >= this number
    buyVia: Optional[str] = None  # Which shopping site, if any, to buy from
    onlineShopOptions: Optional[
        List[ShopOption]
    ] = None  # Product IDs to buy, in preference order

    def validate(self) -> None:
        if self.buyVia is not None:
            if self.onlineShopOptions is None:
                raise KeyError("Missing onlineShopOptions when buyVia was set")
            if len(self.onlineShopOptions) == 0:
                raise ValueError("onlineShopOptions must not be empty")


@dataclass
class ShopOption:
    productId: str
    quantity: float
