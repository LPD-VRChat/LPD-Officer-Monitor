# Standard
import logging

# Community
import discord

# Custom
from .base_bl import DiscordListenerBL, bl_listen
import settings

log = logging.getLogger("lpd-officer-monitor")


class TimeBL(DiscordListenerBL):
    @bl_listen("on_message")
    async def process_loa(self, message: discord.Message) -> None:
        if message.channel.id == settings.LEAVE_OF_ABSENCE_CHANNEL:
            log.debug("Processing LOA")
