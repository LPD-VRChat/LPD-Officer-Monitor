from enum import Enum
from _pytest import config
import discord
from sqlalchemy import event
import src.layers.storage.models
import pytest
import settings
import sqlalchemy
import databases
import os
import logging
import pytest_asyncio
import src.layers.storage.models as models
import datetime
import discord.ext.test as dpytest
import sqlite3

from testing.fixtures import dpytest_fixtures
from testing.fixtures.time_fixtures import random_interval_time_between

URL = "sqlite:///test.sqlite"


class OfficerExperiment(Enum):
    inactive = 0
    active = 1
    notenough = 2
    loa = 3
    # TODO: add renew


async def destroy_db():
    assert URL == src.layers.storage.models.DATABASE_URL

    engine = sqlalchemy.create_engine(URL)
    src.layers.storage.models.metadata.drop_all(engine)
    src.layers.storage.models.metadata.create_all(engine)


async def setup_db_data():
    # TODO: add patrol time for officers, pre setup registration so they don't need to happen when bot get `on_ready`

    start = datetime.datetime.now() - datetime.timedelta(
        days=settings.MAX_INACTIVE_DAYS
    )
    end = datetime.datetime.now() - datetime.timedelta(days=1)

    aVc = None
    for vc in dpytest.get_config().channels:
        if isinstance(vc, discord.VoiceChannel):
            await models.SavedVoiceChannel.objects.create(
                id=vc.id,
                name=vc.name,
                guild_id=vc.guild.id,
            )
            aVc = vc

    for rank_index, rank in enumerate(settings.ROLE_LADDER.__dict__.values()):
        for experiment in OfficerExperiment:
            a = (rank_index + 1) * 100 + experiment.value
            officer = await models.Officer.objects.create(
                id=(rank_index + 1) * 100 + experiment.value,
                started_monitoring=start,
                vrchat_name=f"{rank.name.replace('LPD ', '')} {experiment.name}",
                vrchat_id="usr_ffffffff-ffff-ffff-fffffff",
                deleted_at=None,
            )
            officer.id = a  # id gets overwritten by the database
            await officer.update()
            match experiment:
                case OfficerExperiment.inactive:
                    pass
                case OfficerExperiment.active:
                    for i in range(6):
                        patrol_start, patrol_end = random_interval_time_between(
                            start, end, datetime.timedelta(hours=2)
                        )
                        patrol = await models.Patrol.objects.create(
                            officer=officer.id,
                            start=patrol_start,
                            end=patrol_end,
                            event=None,
                            main_channel=aVc.id,
                        )
                case OfficerExperiment.notenough:
                    patrol_start, patrol_end = random_interval_time_between(
                        start,
                        end,
                        datetime.timedelta(hours=1),
                    )
                    patrol = await models.Patrol.objects.create(
                        officer=officer,
                        start=patrol_start,
                        end=patrol_end,
                        event=None,
                        main_channel=aVc.id,
                    )
                case OfficerExperiment.loa:
                    models.LOAEntry.objects.create(
                        officer=officer,
                        start=end - datetime.timedelta(days=7),
                        end=end + datetime.timedelta(days=10),
                        message_id=1234567890,
                        channel_id=1234567890,
                    )

    pass
