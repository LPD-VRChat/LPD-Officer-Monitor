from operator import ge
import pytest
import pytest_asyncio
import discord.ext.test as dpytest
import datetime as dt
import settings

from testing.fixtures.dpytest_fixtures import bot_dispatch
from testing.fixtures.default_data_fixtures import OfficerExperiment, OfficerIdRank


@pytest.mark.asyncio
@pytest.mark.reset_db
async def test_bot_mark_inactive(bl_wrapper, bot, reset_database):
    # TODO: refactor original command to have implementation in business layer instead of duplicating code
    date_from = dt.datetime.now() - dt.timedelta(days=settings.MAX_INACTIVE_DAYS)
    officers_bellow_time = await bl_wrapper.pt_bl.get_officer_bellow_patrol_time(
        date_from,
        settings.MIN_ACTIVITY_MINUTES / 60,
    )

    for officer in officers_bellow_time:
        assert officer.id % 100 in [
            OfficerExperiment.inactive.value,
            OfficerExperiment.notenough.value,
            OfficerExperiment.loa.value,
            OfficerExperiment.renew.value,
        ]
        assert int(officer.id / 100) * 100 in [
            OfficerIdRank.recruit.value,
            OfficerIdRank.officer.value,
            OfficerIdRank.senior_officer.value,
            OfficerIdRank.corporal.value,
        ]

    loas = await bl_wrapper.loa_bl.list_loa()
    renews = await bl_wrapper.loa_bl.list_renewed(date_from)
    inactives = await bl_wrapper.loa_bl.process_inactives(
        officers_bellow_time, loas, renews
    )

    for officer in inactives:
        assert officer.id % 100 in [
            OfficerExperiment.inactive.value,
            OfficerExperiment.notenough.value,
        ]
        assert int(officer.id / 100) * 100 in [
            OfficerIdRank.recruit.value,
            OfficerIdRank.officer.value,
            OfficerIdRank.senior_officer.value,
            OfficerIdRank.corporal.value,
        ]
