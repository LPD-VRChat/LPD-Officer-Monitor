from re import A
import pytest
import discord.ext.test as dpytest
import pytest_asyncio
import asyncio
import os
import logging

from discord import Intents
from discord.ext.commands import Bot

import settings
from src.layers.ui.discord_commands import setup as setup_discord_commands
from testing.fixtures.dpytest_fixtures import setup_LPD_Discord_main
import src.layers.business.bl_wrapper as bl_wrapper_module
from src.layers.storage.models import database
from src.extra_logging import (
    DiscordLoggingHandler,
    CustomFormatter,
    DiscordDebugFilter,
    ExternalFilter,
)
import testing.fixtures.default_data_fixtures
from testing.fixtures.dpytest_fixtures import bot_dispatch

pytest_plugins = [
    "testing.fixtures.discord_fixtures",
    "testing.fixtures.storage_fixtures",
]


# Register custom markers
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "reset_db: mark test to reset database to known state"
    )
    config.addinivalue_line(
        "markers", "ordered: mark test as part of ordered test sequence"
    )


intents = Intents.default()
intents.members = True
intents.presences = True
intents.voice_states = True
intents.messages = True
intents.message_content = True


@pytest_asyncio.fixture
async def bot():
    log = logging.getLogger("lpd-officer-monitor")
    log.setLevel(logging.DEBUG)
    formatter_no_date = CustomFormatter(
        "%(levelname).1s|%(module)-16s| %(message)s",
    )
    sh = logging.StreamHandler()
    sh.addFilter(DiscordDebugFilter())
    log.addHandler(sh)

    event_loop = asyncio.get_running_loop()
    bot = Bot(intents=intents, command_prefix=settings.BOT_PREFIX, loop=event_loop)
    bot.remove_command("help")
    dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(dir)
    # os.chdir("cogs")
    # for filename in os.listdir(os.getcwd()):
    #     if filename.endswith(".py"):
    #         await bot.load_extension(f"cogs.{filename[:-3]}")
    # await bot.load_extension("jishaku")
    await bot._async_setup_hook()
    dpytest.configure(bot)
    setup_LPD_Discord_main()
    await testing.fixtures.default_data_fixtures.setup_db_data()

    async def on_error(event_method: str, /, *args, **kwargs) -> None:
        log.exception("Exception in %s", event_method)
        assert False

    bot.on_error = on_error

    return bot


@pytest_asyncio.fixture
async def bl_wrapper(bot, create_db):
    event_loop = asyncio.get_running_loop()
    assert settings.CONFIG_LOADED == "base_test"
    if not database.is_connected:
        event_loop.run_until_complete(database.connect())

    bl_wrapper = bl_wrapper_module.create(bot)
    event_loop.run_until_complete(setup_discord_commands(bot, bl_wrapper))
    # loop.create_task(start_webmanager(bot, log))
    await dpytest.callbacks.dispatch_event("on_ready")  # internal
    await bot_dispatch(bot, "ready")  # external
    return bl_wrapper


def pytest_sessionfinish(session, exitstatus):
    """Code to execute after all tests."""

    # dat files are created when using attachements
    print("\n-------------------------\nClean dpytest_*.dat files")
    import glob

    fileList = glob.glob("./dpytest_*.dat")
    for filePath in fileList:
        try:
            os.remove(filePath)
        except Exception:
            print("Error while deleting file : ", filePath)
