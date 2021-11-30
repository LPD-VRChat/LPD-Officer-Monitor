# Standard Library Imports
import asyncio
import logging
import os
import sys


def setup_logger():
    import settings
    from src.extra_logging import DiscordLoggingHandler

    log = logging.getLogger("lpd-officer-monitor")
    log.setLevel(logging.DEBUG)
    log_folder = os.path.dirname(settings.LOG_FILE_PATH)
    if not os.path.isdir(log_folder):
        os.makedirs(log_folder)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    sh = logging.StreamHandler()
    fh = logging.FileHandler(settings.LOG_FILE_PATH, encoding="utf-8")
    dh = DiscordLoggingHandler(webhook=settings.LOGGING_WEBHOOK)
    sh.setFormatter(formatter)
    fh.setFormatter(formatter)
    dh.setFormatter(formatter)
    log.addHandler(sh)
    log.addHandler(fh)
    log.addHandler(dh)

    return log


async def start_webmanager(bot, log):
    import nest_asyncio

    from src.layers.ui.server.web_manager import WebManager
    import settings
    import keys

    nest_asyncio.apply()

    log.info(f"Starting WebManager...")
    web_manager = await WebManager.configure(
        bot,
        host=settings.WEB_MANAGER_HOST,
        port=settings.WEB_MANAGER_PORT,
        id=keys.CLIENT_ID,
        secret=keys.CLIENT_SECRET,
        token=keys.DISCORD_TOKEN,
        callback=keys.CALLBACK_URL,
        certfile=keys.CERTFILE,
        keyfile=keys.KEYFILE,
        _run_insecure=False,
    )
    await web_manager.start()


def main():
    os.environ.setdefault("LPD_OFFICER_MONITOR_ENVIRONMENT", "dev")

    ####################
    ### Main Imports ###
    ####################

    # Community Library Imports
    import discord
    import nest_asyncio
    from discord.ext import commands

    # Custom Library Imports
    import keys
    import settings
    from src.layers import business as bl
    from src.layers.business.bl_wrapper import BusinessLayerWrapper
    from src.layers.ui.discord_commands import setup as setup_discord_commands

    ##############################
    ### Setup Global Variables ###
    ##############################

    loop = asyncio.get_event_loop()
    nest_asyncio.apply()

    intents = discord.Intents.default()
    intents.members = True

    bot = commands.Bot(command_prefix=settings.BOT_PREFIX, intents=intents)
    bot.remove_command("help")

    bot.has_been_started = False
    bot.everything_ready = False

    #####################
    ### Setup logging ###
    #####################

    log = setup_logger()

    ##################################
    ### Start the different layers ###
    ##################################

    # Business layers
    time_bl = bl.TimeBL(bot)
    vrc_bl = bl.VRChatBL()
    p_bl = bl.ProgrammingBL(bot)
    web_bl = bl.WebManagerBL(bot)
    bl_wrapper = BusinessLayerWrapper(
        bot, time_bl=time_bl, vrc_bl=vrc_bl, p_bl=p_bl, web_bl=web_bl
    )

    # UI Layers
    setup_discord_commands(bot, bl_wrapper)
    loop.create_task(start_webmanager(bot, log))

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

        bot.guild = bot.get_guild(settings.SERVER_ID)
        if bot.guild:
            log.info(f"{'Server name':<12}: {bot.guild.name}")
            log.info(f"{'Server ID':<12}: {bot.guild.id}")
        else:
            await bl_wrapper.clean_shutdown(location="internal", by="server lookup")

        if bot.has_been_started:
            await bl_wrapper.clean_shutdown(
                location="internal", by="automatic recovery", exit=False
            )

        # This should be the last line in this function
        bot.has_been_started = True

    @bot.event
    async def on_message(message: discord.Message) -> None:

        # Only process commands that are in a command channel
        if message.channel.id in settings.ALLOWED_COMMAND_CHANNELS:
            await bot.process_commands(message)

    @bot.event
    async def on_command_error(ctx, exception):
        exception_string = str(exception).replace(
            "raised an exception", "encountered a problem"
        )

        try:
            await ctx.send(exception_string)
        except discord.Forbidden:
            bot.get_channel(settings.ERROR_LOG_CHANNEL).send(
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
            await bot.start(keys.DISCORD_TOKEN)
        finally:
            if not bot.is_closed():
                await bot.close()

    future = asyncio.ensure_future(runner(), loop=loop)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(bl_wrapper.clean_shutdown())


if __name__ == "__main__":
    main()
    os.execv(sys.executable, ["python"] + sys.argv)