from dataclasses import dataclass
from datetime import datetime


@dataclass
class LarderItem:
    name: str
    checkFrequencyDays: int
    lastChecked: datetime  # Epoch seconds
    quantity: int
    replaceAt: int  # Buy if fewer than this
