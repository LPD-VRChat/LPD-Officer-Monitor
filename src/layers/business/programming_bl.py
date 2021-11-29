# Standard
from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
from os import _exit
import logging

# Community
from discord.ext import commands

# Custom
import settings
from src.layers.business.base_bl import DiscordListenerBL

if TYPE_CHECKING:
    from .bl_wrapper import BusinessLayerWrapper


log = logging.getLogger("lpd-officer-monitor")


class ProgrammingBL(DiscordListenerBL):
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

        # Stop the event loop
        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(loop.stop)

        if exit:
            _exit(0)
