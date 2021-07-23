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
from nest_asyncio import apply

# Community Library Imports
import discord
from discord.errors import HTTPException
from discord.ext import commands

# Custom Library Imports
from UILayer.DiscordCommands import setup as setup_commands
from BusinessLayer.DiscordEvents import setup as setup_events
from BusinessLayer.DiscordChecks import setup as setup_checks

from BusinessLayer.extra_functions import clean_shutdown

apply()

loop = asyncio.get_event_loop()

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=Settings.BOT_PREFIX, intents=intents)
bot.remove_command("help")
bot.guild = bot.get_guild(Settings.SERVER_ID)

bot.has_been_started = False
bot.everything_ready = False
bot.shutdown = clean_shutdown

#######################################################################
### Add DiscordChecks, DiscordEvents and DiscordCommands to the bot ###
#######################################################################

setup_checks(bot)
setup_events(bot)
setup_commands(bot)


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
