# Standard
from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
from os import _exit
import logging

# Community
import discord
from discord.ext import commands

# Custom
import settings
from src.layers.business.base_bl import DiscordListenerMixin
from src.layers.storage.models import database

if TYPE_CHECKING:
    from .bl_wrapper import BusinessLayerWrapper


log = logging.getLogger("lpd-officer-monitor")


class ProgrammingBL(DiscordListenerMixin):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot

    async def clean_shutdown(
        self,
        location: str = "the console",
        shutdown_by: str = "KeyboardInterrupt",
        exit: bool = True,
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

        if exit:
            _exit(0)
