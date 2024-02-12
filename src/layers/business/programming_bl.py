# Standard
from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import asyncio
from os import _exit
import logging

# Community
import discord
from discord.ext import commands

# Custom
import settings
from src.layers.business.base_bl import DiscordListenerMixin, bl_listen
from src.layers.storage.models import database

if TYPE_CHECKING:
    from .bl_wrapper import BusinessLayerWrapper


log = logging.getLogger("lpd-officer-monitor")

HOW_TO_FIX = """
Make sure you turn off `Legacy chat input` in `Accessibility`.
Make sure when you are typing the command that Discord is showing the command name back with a description.
If the name of the command isn't suggested to you, you do no have the rights to execute it.
"""


class ProgrammingBL(DiscordListenerMixin):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        super().__init__()

    async def clean_shutdown(
        self,
        location: str = "the console",
        shutdown_by: str = "KeyboardInterrupt",
        exit_code: Optional[int] = None,
    ):
        """
        Cleanly shutdown the bot.
        """

        # Log the shutdown
        msg_string = f"Bot {'shut down' if exit else 'restarted'} from {location} by {shutdown_by}"
        if location == "the console":
            print()
        log.warning(msg_string)

        # self.bot.dispatch("shutdown")
        # this creates a task that get's wiped because of exit or loop stop
        for event in self.bot.extra_events.get("on_unload", []):
            # WARNING: `extra_events` accessing none documented public variable !!!
            try:
                await discord.utils.maybe_coroutine(event)
            except:
                log.exception("Failed to call `on_unload`")

        # Stop the database
        if database.is_connected:
            await database.disconnect()

        # Stop the event loop
        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(loop.stop)

        if exit_code:
            _exit(exit_code)

    @bl_listen("on_message")
    async def detect_slash_cmd_fail(self, message: discord.Message):
        if (
            message.author.bot
            or message.channel.id not in settings.ALLOWED_COMMAND_CHANNELS
        ):
            return
        if message.content.startswith("/"):
            try:
                await message.reply(
                    """:red_circle::red_circle:The command didn't work.:red_circle::red_circle:"""
                    + HOW_TO_FIX
                )
            except discord.errors.Forbidden:
                log.warn(
                    f"Fail to write to channel <#{message.channel.id}> to warn about slash fail"
                )
                try:
                    await message.author.send(
                        f":red_circle::red_circle:The command in <#{message.channel.id}> didn't work.:red_circle::red_circle:"
                        + HOW_TO_FIX
                    )
                except discord.errors.Forbidden:
                    log.warn(
                        f"Fail to send a message to <@{message.author.id}> to warn about slash fail"
                    )
