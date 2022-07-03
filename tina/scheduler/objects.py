from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScheduledAction:
    actionKey: str


@dataclass
class ScheduleEntry:
    timeUtc: datetime
    action: ScheduledAction
