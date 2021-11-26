# Standard
import logging

# Community
import discord

# Custom
from .base_bl import BaseBL, bl_listen
import Settings

log = logging.getLogger("lpd-officer-monitor")

class TimeBL(BaseBL):
    @bl_listen("on_message")
    async def process_loa(self, message: discord.Message) -> None:
        if message.channel.id == Settings.LEAVE_OF_ABSENCE_CHANNEL:
            log.debug("Processing LOA")
