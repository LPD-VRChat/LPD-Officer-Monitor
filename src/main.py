# Standard Library Imports
import asyncio
import logging
import os
import sys
import traceback
import signal

# need python 3.10 for match instruction
assert (
    sys.version_info.major == 3 and sys.version_info.minor >= 10
), f"need python 3.10.x or up. got {sys.version.split(' ')[0] }"

# Community Library Imports
import discord

assert discord.__version__.startswith(
    "2.0."
), f"Discord.py wrong version, got {discord.__version__}, expected 2.0.x"
import nest_asyncio
from discord.ext import commands

# Custom Library Imports
import settings
from src.layers import business as bl
import src.layers.business.bl_wrapper as bl_wrapper
from src.layers.ui.discord_commands import setup as setup_discord_commands

# from src.layers.ui.server.web_manager import WebManager
from src.extra_logging import DiscordLoggingHandler
from src.layers.storage.models import database
from src.layers.business.extra_functions import interaction_reply


nest_asyncio.apply()


def setup_logger():
    log = logging.getLogger("lpd-officer-monitor")
    log.propagate = False
    log.setLevel(logging.DEBUG)
    log_folder = os.path.dirname(settings.LOG_FILE_PATH)
    if not os.path.isdir(log_folder):
        os.makedirs(log_folder)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname).1s %(module).12s | %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )
    sh = logging.StreamHandler()
    dh = DiscordLoggingHandler(webhook=settings.LOGGING_WEBHOOK)
    sh.setFormatter(formatter)
    dh.setFormatter(formatter)
    log.addHandler(sh)
    log.addHandler(dh)
    if not os.environ.get("LPD_OFFICER_MONITOR_DOCKER"):
        # TODO fix file logging in Docker
        fh = logging.FileHandler(settings.LOG_FILE_PATH, encoding="utf-8")
        fh.setFormatter(formatter)
        log.addHandler(fh)

    return log


async def start_webmanager(bot, log):
    return
    log.debug(f"Starting WebManager...")
    web_manager = await WebManager.configure(
        bot,
        host=settings.WEB_MANAGER_HOST,
        port=settings.WEB_MANAGER_PORT,
        id=settings.CLIENT_ID,
        secret=settings.CLIENT_SECRET,
        token=settings.DISCORD_TOKEN,
        callback=settings.CALLBACK_URL,
        certfile=settings.CERTFILE,
        keyfile=settings.KEYFILE,
        _run_insecure=False,
    )
    await web_manager.start()


async def tree_on_error(
    interaction: discord.Interaction, error: discord.app_commands.AppCommandError
):
    log = logging.getLogger("lpd-officer-monitor")
    if isinstance(error, discord.app_commands.CheckFailure):
        ##check interaction for responce type
        for check in interaction.command.checks:
            try:
                r: bool = await discord.utils.maybe_coroutine(check, interaction)
            except BaseException as err:
                log.exception(
                    f"tree_error chk `{interaction.command.name}` u={interaction.user.id} c={interaction.channel_id}\n{err}"
                )
                if settings.CONFIG_LOADED == "dev":
                    await interaction_reply(
                        interaction,
                        f"🛠️dev :red_circle:check failed!!! {err}",
                        ephemeral=True,
                    )
                else:
                    await interaction_reply(
                        interaction,
                        f":red_circle: Unauthrorized Command or wrong channel",
                        ephemeral=True,
                    )
                return
            if not r:
                if settings.CONFIG_LOADED == "dev":
                    await interaction_reply(
                        interaction,
                        f"🛠️dev :red_circle:check denied: {check.__qualname__}",
                        ephemeral=True,
                    )
                else:
                    await interaction_reply(
                        interaction,
                        f":red_circle: Unauthrorized Command or wrong channel",
                        ephemeral=True,
                    )
                if settings.LOG_PERMISSION_DENIED_ENABLE:
                    log.log(
                        settings.LOG_PERMISSION_DENIED_LEVEL,
                        f"perm chk deny u={interaction.user.id} c={interaction.channel_id} {check.__qualname__}",
                    )
                return
    if isinstance(error, discord.app_commands.CommandInvokeError):
        log.error(str(error.original))
        traceback.print_exception(
            type(error.original), error.original, error.original.__traceback__
        )
    else:
        log.error(
            f"cmd tree unk err `{interaction.command.name}` u={interaction.user.id} c={interaction.channel_id}\n{error}"
        )

    await interaction_reply(
        interaction, f":red_circle: Internal error :red_circle:", ephemeral=True
    )


def main():
    ##############################
    ### Setup Global Variables ###
    ##############################

    loop = asyncio.get_event_loop()
    nest_asyncio.apply()

    intents = discord.Intents.default()
    intents.members = True
    intents.presences = True
    intents.voice_states = True
    intents.messages = True
    intents.message_content = True

    bot = commands.Bot(command_prefix=settings.BOT_PREFIX, intents=intents)
    bot.remove_command("help")

    bot.has_been_started = False
    bot.everything_ready = False

    bot.tree.on_error = tree_on_error

    #####################
    ### Setup logging ###
    #####################

    log = setup_logger()

    ##################################
    ### Start the different layers ###
    ##################################

    # Database
    # Make sure the database is started when we start everything else
    if not database.is_connected:
        loop.run_until_complete(database.connect())

    # UI Layers
    loop.run_until_complete(setup_discord_commands(bot, bl_wrapper.create(bot)))
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
        log.debug(f"{'Logged in as':<18}: {bot.user.name}")
        log.debug(f"{'Loaded settings':<18}: {settings.CONFIG_LOADED}")

        bot.guild = bot.get_guild(settings.SERVER_ID)
        if bot.guild:
            log.debug(f"{'Server name':<18}: {bot.guild.name}")
            log.debug(f"{'Server ID':<18}: {bot.guild.id}")
        else:
            if settings.CLIENT_ID == 0:
                log.error("CLIENT_ID not defined, cannot generate invite link")
            else:
                invite_url = discord.utils.oauth_url(
                    settings.CLIENT_ID,
                    permissions=discord.Permissions(
                        permissions=settings.DISCORD_PERMISSION
                    ),
                )
                log.warning(f"bot invite url {invite_url}")
            await bot.cogs["Programming"].bl_wrapper.p.clean_shutdown(
                location="internal",
                shutdown_by="server lookup",
                exit_code=69,  # EX_UNAVAILABLE
            )

        if bot.has_been_started:
            await bot.cogs["Programming"].bl_wrapper.p.clean_shutdown(
                location="internal", shutdown_by="automatic recovery"
            )

        # This should be the last line in this function
        bot.has_been_started = True

    @bot.event
    async def on_message(message: discord.Message) -> None:
        # Only process commands that are in a command channel
        if message.channel.id in settings.ALLOWED_COMMAND_CHANNELS:
            await bot.process_commands(message)

    @bot.event
    async def on_command_error(ctx: discord.ext.commands.Context, exception):
        exception_string = str(exception).replace(
            "raised an exception", "encountered a problem"
        )

        if isinstance(exception, discord.ext.commands.errors.CheckFailure):
            if isinstance(exception, discord.ext.commands.CheckAnyFailure):
                if settings.CONFIG_LOADED == "dev":
                    ctx.send(f"🛠️dev check any denied", ephemeral=True)
                else:
                    await ctx.send(
                        ":red_circle: Unauthrorized Command or wrong channel"
                    )
                if settings.LOG_PERMISSION_DENIED_ENABLE:
                    log.log(
                        settings.LOG_PERMISSION_DENIED_LEVEL,
                        f"perm chkany deny u={ctx.author.id} c={ctx.channel.id} {ctx.command.name}",
                    )
                return
            for chk in ctx.command.checks:
                try:
                    r = await discord.utils.maybe_coroutine(chk, ctx)
                except (commands.CheckFailure, commands.CheckAnyFailure) as e:
                    r = False
                except:
                    import traceback

                    print("".join(traceback.format_exc()))
                    r = False
                if not r:
                    if settings.CONFIG_LOADED == "dev":
                        await ctx.send(
                            f"🛠️dev check deny: {getattr(chk,'__qualname__')}",
                            ephemeral=True,
                        )
                    else:
                        await ctx.send(
                            ":red_circle: Unauthrorized Command or wrong channel"
                        )
                    if settings.LOG_PERMISSION_DENIED_ENABLE:
                        log.log(
                            settings.LOG_PERMISSION_DENIED_LEVEL,
                            f"perm chkany deny u={ctx.author.id} c={ctx.channel.id} {ctx.command.name}",
                        )
                    return
            if settings.CONFIG_LOADED == "dev":
                await ctx.send(f"🛠️dev check failed: unknown", ephemeral=True)
            else:
                await ctx.send(":red_circle: Unauthrorized Command or wrong channel")
            log.error(
                f"u={ctx.author.id} `{ctx.invoked_with}` unknown CheckFailure {exception_string}"
            )
            return
        try:
            if settings.CONFIG_LOADED == "dev":
                await ctx.send("🛠️dev :red_circle: Error " + exception_string)
            else:
                await ctx.send(":red_circle: Internal error :red_circle:")
        except discord.Forbidden:
            bot.get_channel(settings.ERROR_LOG_CHANNEL).send(
                f"**{ctx.author}**, I'm not allowed to send messages in {ctx.channel}**"
            )
            pass

        # Skip logging the exception if the user just messed up the input to a command
        if exception_string.find("encountered a problem") != -1:
            log.log(logging.ERROR, exception_string, exc_info=exception)
        else:
            log.error(
                f"cmdErr u={ctx.author.id} c={ctx.channel.id} {ctx.command.name} {exception_string}"
            )

    @bot.event
    async def on_error(event, *args, **kwargs):
        log.exception(f'Error encountered in event "{event}"')

    #####################
    ### Start the bot ###
    #####################

    async def runner():
        try:
            await bot.start(settings.DISCORD_TOKEN)
        finally:
            if not bot.is_closed():
                await bot.close()

    def raise_graceful_exit(sig, *args):
        log.info(f"EXIT signal {sig}")
        raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, raise_graceful_exit)
    signal.signal(signal.SIGTERM, raise_graceful_exit)
    if hasattr(signal, "SIGHUP"):  # only in linux
        signal.signal(signal.SIGHUP, raise_graceful_exit)

    future = asyncio.ensure_future(runner(), loop=loop)
    try:
        # Make sure we don't silently drop errors
        loop.run_until_complete(future)
    except KeyboardInterrupt:
        loop.run_until_complete(
            bot.cogs["Programming"].bl_wrapper.p.clean_shutdown()
        )  # this is ugly or it's a global var ...
