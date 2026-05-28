import pytest
import pytest_asyncio
import discord.ext.test as dpytest
import datetime as dt
import settings

from src.layers.storage import special_queries
from testing.fixtures.default_data_fixtures import OfficerExperiment, OfficerIdRank


@pytest.mark.asyncio
@pytest.mark.reset_db
async def test_bot_active_officers(bl_wrapper):
    end = dt.datetime.now(dt.UTC)
    start = end - dt.timedelta(days=90)
    actives = await special_queries.get_active_officers(2, start, end)
    for officer in actives:
        assert officer % 100 in [
            OfficerExperiment.active.value,
        ]
    all = await special_queries.get_active_officers(0, start, end)
    for officer in all:
        assert officer % 100 in [
            OfficerExperiment.notenough.value,
            OfficerExperiment.active.value,
        ]
    print("DONE")


@pytest.mark.asyncio
@pytest.mark.reset_db
async def test_get_sum_patrol_time(bl_wrapper):
    end = dt.datetime.now(dt.UTC)
    start = end - dt.timedelta(days=90)
    leaderboard = await special_queries.get_sum_patrol_time(start, end)
    for officer in leaderboard:
        match (officer % 100):
            case OfficerExperiment.active.value:
                assert leaderboard[officer] == dt.timedelta(seconds=43200)
            case OfficerExperiment.notenough.value:
                assert leaderboard[officer] == dt.timedelta(seconds=3600)
            case _:
                assert False
