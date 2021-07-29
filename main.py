# Set environment to DEV and import Settings and Keys - remove these lines if using production
import os

os.environ.setdefault("LPD_OFFICER_MONITOR_ENVIRONMENT", "dev")

import Settings
import Keys


####################
### Main Imports ###
####################

# Standard Library Imports
import asyncio
import logging
from queue import SimpleQueue
import threading

# Community Library Imports
import discord
from discord.errors import HTTPException
from discord.ext import commands
import nest_asyncio

# Custom Library Imports
from UILayer.DiscordCommands import setup as setup_commands
from BusinessLayer.bl_wrapper import BusinessLayerWrapper
from extra_logging import setup_logging_queue, DiscordLoggingHandler


##############################
### Setup Global Variables ###
##############################

loop = asyncio.get_event_loop()
nest_asyncio.apply()

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=Settings.BOT_PREFIX, intents=intents)
bot.remove_command("help")

bot.has_been_started = False
bot.everything_ready = False


#####################
### Setup logging ###
#####################

log = logging.getLogger("lpd-officer-monitor")
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())
log.addHandler(logging.FileHandler(filename=Settings.LOG_FILE_PATH, encoding="utf-8"))
log.addHandler(DiscordLoggingHandler(bot=bot, channel_id=Settings.ERROR_LOG_CHANNEL))
logging_thread = threading.Thread(target=setup_logging_queue)
logging_thread.start()


##################################
### Start the different layers ###
##################################

bl_wrapper = BusinessLayerWrapper(bot)
setup_commands(bot, bl_wrapper)


#####################
### Start the bot ###
#####################


async def runner():
    try:
        await bot.start(Keys.DISCORD_TOKEN)
    finally:
        if not bot.is_closed():
            await bot.close()


future = asyncio.ensure_future(runner(), loop=loop)
try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(bot.shutdown(bot))
