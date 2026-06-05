
from datetime import datetime, timedelta
from datetime import UTC


def utc_now():
    return datetime.now(tz=UTC)


def plus_seconds(seconds: int) -> datetime:
    return utc_now() + timedelta(seconds=seconds)

