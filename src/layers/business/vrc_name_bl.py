# Standard
import logging
from typing import Optional
import json
import os
import subprocess

# external
import discord
from discord.ext import commands

# Custom
import settings
from .base_bl import DiscordListenerMixin, bl_listen
from src.layers.storage import models
from settings.classes import RoleLadderElement
from src.layers.business.extra_functions import has_role_id

log = logging.getLogger("lpd-officer-monitor")


class VRChatBL(DiscordListenerMixin):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        super().__init__()
