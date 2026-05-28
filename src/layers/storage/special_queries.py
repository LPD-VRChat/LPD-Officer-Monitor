from typing import Dict
import settings

from src.layers.storage import models

import databases
import sqlalchemy

import datetime as dt

# SQLite as different function available, we have to work around that
if models.DATABASE_URL.startswith("sqlite"):
    _PATROL_LEN_SQL_COLUMN = "SUM((unixepoch(end) - unixepoch(start))) AS patrol_length"
else:
    #mariaDB
    _PATROL_LEN_SQL_COLUMN = "SUM(TIMESTAMPDIFF(SECOND, start,end)) AS 'patrol_length'"


async def get_active_officers(
    minimum_activity: float,
    start: dt.datetime,
    end: dt.datetime,
) -> set[int]:
    async with models.database.connection() as conn:
        result = await conn.execute(
            sqlalchemy.text("""SELECT
                    officer,
                    """+_PATROL_LEN_SQL_COLUMN+"""
                FROM patrols
                WHERE start < :enddt and end > :startdt
                GROUP BY officer
                HAVING patrol_length > :min_patrol_len;"""),
            {
                "min_patrol_len": minimum_activity * 3600,
                "enddt": end,
                "startdt": start,
            },
        )

        rows = result.fetchall()
    return [r[0] for r in rows]


async def get_sum_patrol_time(
    from_dt: dt.datetime, to_dt: dt.datetime
) -> Dict[int, dt.timedelta]:
    """drop in replacement for `pt_bl.get_top_patrol_time`"""
    async with models.database.connection() as conn:
        result = await conn.execute(
            sqlalchemy.text("""SELECT `officer`,"""
                +_PATROL_LEN_SQL_COLUMN+
"""         FROM `patrols`
            WHERE start < :enddt and end > :startdt
            GROUP BY `officer`
            ORDER BY `patrol_length` DESC"""),
            {
                "enddt": to_dt,
                "startdt": from_dt,
            },
        )
        rows = result.fetchall()
    return {k: dt.timedelta(seconds=int(v)) for k, v in rows}
