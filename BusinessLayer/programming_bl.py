# Standard
from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
from os import _exit
import logging

# Community
from discord.ext import commands

# Custom
import Settings
from BusinessLayer.base_bl import BaseBL

if TYPE_CHECKING:
    from .bl_wrapper import BusinessLayerWrapper


log = logging.getLogger("lpd-officer-monitor")


class ProgrammingBL(BaseBL):
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
        log.warning(msg_string)

        if exit:
            # Stop the event loop and exit Python. The OS should be
            # calling this script inside a loop if you want the bot to restart
            loop = asyncio.get_event_loop()
            loop.stop()
            _exit(0)
