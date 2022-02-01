# Standard
import logging
import nest_asyncio

# Community
import discord

# Custom
from .base_bl import DiscordListenerBL, bl_listen
from src.layers.ui.server.web_manager import WebManager
import settings

nest_asyncio.apply()

log = logging.getLogger("lpd-officer-monitor")


class WebManagerBL(DiscordListenerBL):
    @bl_listen("on_ready")
    async def start_web_manager(self):
        pass
