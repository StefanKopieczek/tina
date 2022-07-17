from datetime import datetime, timezone


def to_epoch_time(time: datetime):
    return int(time.timestamp())


def parse_epoch_time(epoch_time: int):
    return datetime.fromtimestamp(epoch_time, timezone.utc)
