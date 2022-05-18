# Standard
import logging
import nest_asyncio

# Community
from discord.ext import commands

# Custom
from .base_bl import DiscordListenerMixin, bl_listen
from src.layers.ui.server.web_manager import WebManager
import settings

nest_asyncio.apply()

log = logging.getLogger("lpd-officer-monitor")


class WebManagerBL(DiscordListenerMixin):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot

    @bl_listen("on_ready")
    async def start_web_manager(self):
        pass
