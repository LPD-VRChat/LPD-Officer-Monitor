from typing import Dict
import settings

from src.layers.storage import models

import databases
import sqlalchemy

import datetime as dt


async def get_active_officers(
    minimum_activity: float,
    start: dt.datetime,
    end: dt.datetime,
) -> list[int]:
    result = await models.database.fetch_all(
        query="""SELECT `officer`, SUM(TIMESTAMPDIFF(SECOND, start,end)) AS 'patrol_length'
        FROM `patrols`
        WHERE start < :enddt and end > :startdt
        GROUP BY `officer`
        HAVING patrol_length > :min_patrol_len""",
        values={
            "min_patrol_len": minimum_activity * 3600,
            "enddt": end,
            "startdt": start,
        },
    )
    return result


async def get_sum_patrol_time(
    from_dt: dt.datetime, to_dt: dt.datetime
) -> Dict[int, dt.timedelta]:
    """drop in replacement for `pt_bl.get_top_patrol_time`"""
    result = await models.database.fetch_all(
        query="""SELECT `officer`, SUM(TIMESTAMPDIFF(SECOND, start,end)) AS 'patrol_length'
        FROM `patrols`
        WHERE start < :enddt and end > :startdt
        GROUP BY `officer`""",
        values={
            "enddt": to_dt,
            "startdt": from_dt,
        },
    )
    return {k: int(v) for k, v in sorted(result, key=lambda x: int(x[1]), reverse=True)}
