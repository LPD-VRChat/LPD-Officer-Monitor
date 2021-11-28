# Standard
import logging
import nest_asyncio

# Community
import discord

# Custom
from .base_bl import BaseBL, bl_listen
from src.layers.ui.server.web_manager import WebManager
import settings
import keys

nest_asyncio.apply()

log = logging.getLogger("lpd-officer-monitor")


class WebManagerBL(BaseBL):
    @bl_listen("on_ready")
    async def start_web_manager(self):
        log.info(f"Starting WebManager...")
        self.bot.web_manager = await WebManager.configure(
            self.bot,
            host=settings.WEB_MANAGER_HOST,
            port=settings.WEB_MANAGER_PORT,
            id=keys.CLIENT_ID,
            secret=keys.CLIENT_SECRET,
            token=keys.DISCORD_TOKEN,
            callback=keys.CALLBACK_URL,
            certfile=keys.CERTFILE,
            keyfile=keys.KEYFILE,
            _run_insecure=False,
        )
        await self.bot.web_manager.start()
