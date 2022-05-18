# Standard
from dataclasses import dataclass
import datetime as dt
from enum import Enum
import logging
from typing import Union

# Community
import discord
from discord.ext import commands

# Custom
import settings
from src.layers.business.extra_functions import is_lpd_member
from src.layers.storage.models import Officer
from .base_bl import DiscordListenerMixin, EventSenderMixin, bl_listen

log = logging.getLogger("lpd-officer-monitor")


class TimeBL(DiscordListenerMixin):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @bl_listen("on_message")
    async def process_loa(self, message: discord.Message) -> None:
        if message.channel.id == settings.LEAVE_OF_ABSENCE_CHANNEL:
            log.debug("Processing LOA")
