import datetime
import random


def random_time_between(
    start: datetime.datetime, end: datetime.datetime
) -> datetime.datetime:
    return start + datetime.timedelta(
        seconds=random.randint(0, int((end - start).total_seconds()))
    )


def random_interval_time_between(
    start: datetime.datetime, end: datetime.datetime, interval: datetime.timedelta
) -> tuple[datetime.datetime, datetime.datetime]:
    assert start + interval < end
    rng = random.randint(0, int((end - start - interval).total_seconds()))
    return (
        start + datetime.timedelta(seconds=rng),
        start + interval + datetime.timedelta(seconds=rng),
    )
