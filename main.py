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
import threading

# Community Library Imports
import discord
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
log.setLevel(logging.DEBUG)
if not os.path.exists(Settings.LOG_FILE_PATH):
    os.makedirs("/".join(Settings.LOG_FILE_PATH.split("/")[:-1]))
    os.close(os.open(Settings.LOG_FILE_PATH, os.O_CREAT))
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
sh = logging.StreamHandler()
fh = logging.FileHandler(Settings.LOG_FILE_PATH, encoding="utf-8")
dh = DiscordLoggingHandler(bot, channel_id=Settings.ERROR_LOG_CHANNEL)
sh.setFormatter(formatter)
fh.setFormatter(formatter)
dh.setFormatter(formatter)
log.addHandler(sh)
log.addHandler(fh)
log.addHandler(dh)
logging_thread = threading.Thread(target=setup_logging_queue)
logging_thread.start()


##################################
### Start the different layers ###
##################################

bl_wrapper = BusinessLayerWrapper(bot)
setup_commands(bot, bl_wrapper)


############################
### Global events/checks ###
############################


@bot.check
def dms_not_supported(ctx):
    if ctx.guild is None:
        log.debug(f"{ctx.author} tried to DM me in {ctx.channel}")
        raise commands.NoPrivateMessage(
            "This bot does not support direct messages. Please use a server channel instead."
        )
    else:
        return True


@bot.event
async def on_ready():
    log.info(f"{'Logged in as':<12}: {bot.user.name}")

    bot.guild = bot.get_guild(Settings.SERVER_ID)
    if bot.guild:
        log.info(f"{'Server name':<12}: {bot.guild.name}")
        log.info(f"{'Server ID':<12}: {bot.guild.id}")
    else:
        await bl_wrapper.clean_shutdown(location="internal", by="server lookup")

    if bot.has_been_started:
        await bl_wrapper.clean_shutdown(
            location="internal", by="automatic recovery", exit=False
        )

    # Call all events that should be called when the bot is ready
    await asyncio.gather(*[e() for e in bl_wrapper.on_ready_events])

    # This should be the last line in this function
    bot.has_been_started = True


@bot.event
async def on_message(message: discord.Message) -> None:

    # Only process commands that are in a command channel
    if message.channel.id in Settings.ALLOWED_COMMAND_CHANNELS:
        await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, exception):
    exception_string = str(exception).replace(
        "raised an exception", "encountered a problem"
    )

    try:
        await ctx.send(exception_string)
    except discord.Forbidden:
        bot.get_channel(Settings.ERROR_LOG_CHANNEL).send(
            f"**{ctx.author}**, I'm not allowed to send messages in {ctx.channel}**"
        )
        pass

    # Skip logging the exception if the user just messed up the input to a command
    if exception_string.find("encountered a problem") != -1:
        log.exception(exception_string)


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
    loop.run_until_complete(bl_wrapper.clean_shutdown())
