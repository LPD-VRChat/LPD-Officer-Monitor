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
