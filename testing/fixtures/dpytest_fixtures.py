import logging
import asyncio

import discord
import discord.ext.test as dpytest
from discord.ext.test.backend import make_voice_channel
from discord.mentions import default

import settings
from testing.fixtures import default_data_fixtures


"""
All helper functions to run the test and fill the gap for things dpytest doesn't support/implement

"""


def make_role_from_settings(
    name: str,
    guild: discord.Guild,
    id_num: int = -1,
) -> discord.Role:

    fake_role = dpytest.backend.make_role(
        name=name.replace("_ROLE", "").replace("_", " ").title(),
        guild=guild,
        id_num=id_num if id_num is not 0 else -1,
    )

    return fake_role


def setup_LPD_Discord_roles(guild: discord.Guild):
    for rank in settings.ROLE_LADDER.__dict__.values():
        fake_role = make_role_from_settings(rank.name, guild, rank.id)
    for name, val in settings.__dict__.items():
        if name.startswith("_"):
            continue
        if name.endswith("_ROLE"):
            fake_role = make_role_from_settings(name, guild, val)


def setup_LPD_Discord_text_channels(guild: discord.Guild) -> list[discord.TextChannel]:
    channels = []
    for name, val in settings.__dict__.items():
        if name.startswith("_"):
            continue
        if name.endswith("_CHANNEL"):
            channels.append(
                dpytest.backend.make_text_channel(
                    name=name.replace("_CHANNEL", "").replace("_", " ").title(),
                    guild=guild,
                    id_num=val,
                )
            )
    return channels


def setup_LPD_members(guild: discord.Guild) -> list[discord.Member]:
    cavies = []

    civillian = dpytest.backend.make_user(
        username="civillian",
        discrim=1,
        id_num=99999,
    )
    dpytest.backend.make_member(
        user=civillian,
        guild=guild,
    )

    for rank_index, rank in enumerate(settings.ROLE_LADDER.__dict__.values()):
        for experiment in default_data_fixtures.OfficerExperiment:
            user = dpytest.backend.make_user(
                username=f"{rank.name.replace('LPD ', '')} {experiment.name}",
                discrim=1,
                id_num=(rank_index + 1) * 100 + experiment.value,
            )

            guinea_pig = dpytest.backend.make_member(
                user=user,
                guild=guild,
                roles=[
                    guild.get_role(rank.id),
                    guild.get_role(settings.LPD_ROLE),
                ],
            )
            cavies.append(guinea_pig)

    return cavies


def setup_LPD_Discord_main():
    test_guild = dpytest.backend.make_guild(name="LPD test", id_num=settings.SERVER_ID)
    setup_LPD_Discord_roles(test_guild)
    txt_channels = setup_LPD_Discord_text_channels(test_guild)

    for i, cat in enumerate(settings.ON_DUTY_CATEGORIES):
        dpytest.backend.make_category_channel(
            name=f"On Duty {i+1}",
            guild=test_guild,
            id_num=cat,
        )
    vc = dpytest.backend.make_voice_channel(
        name="Alpha-00", guild=test_guild, parent_id=settings.ON_DUTY_CATEGORIES[0]
    )
    cavies = setup_LPD_members(test_guild)

    # dpytest generates guilds/channels automatically, but we want to use our own ids
    dpytest_config = dpytest.get_config()
    dpytest_config.guilds.clear()
    dpytest_config.guilds.append(test_guild)
    dpytest_config.channels.clear()
    dpytest_config.channels.extend(txt_channels)
    dpytest_config.channels.append(vc)
    dpytest_config.members.extend(cavies)
    # print("dpytest config: ", dpytest.runner.get_config())


async def bot_dispatch(
    bot: discord.Client,
    event_name: str,
    timeout: int = 10,
    *args,
    **kwargs,
):
    """
    we need to make sure those events are completed.
    sadly we need to reimplement discord/ext/commands/bot.py:dispatch()
    """
    futures = []
    ev = "on_" + event_name
    for event in bot.extra_events.get(ev, []):
        futures.append(bot._schedule_event(event, ev, *args, **kwargs))  # type: ignore

    for i in range(timeout):
        await asyncio.sleep(1)
        for f in futures:
            if not f.done():
                break
        else:
            return

    for f in futures:
        if not f.done():
            f.cancel()
            raise TimeoutError(f"Event {event_name} timed out after {timeout} seconds")
