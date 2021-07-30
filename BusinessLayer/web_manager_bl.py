# Standard
import logging
import nest_asyncio

# Community
import discord

# Custom
from .base_bl import BaseBL, bl_listen
from UILayer.WebManager import WebManager
import Settings
import Keys

nest_asyncio.apply()

log = logging.getLogger("lpd-officer-monitor")


class WebManagerBL(BaseBL):
    @bl_listen("on_ready")
    async def start_web_manager(self):
        log.info(f"Starting WebManager...")
        self.bot.web_manager = await WebManager.configure(
            self.bot,
            host=Settings.WEB_MANAGER_HOST,
            port=Settings.WEB_MANAGER_PORT,
            id=Keys.CLIENT_ID,
            secret=Keys.CLIENT_SECRET,
            token=Keys.DISCORD_TOKEN,
            callback=Keys.CALLBACK_URL,
            certfile=Keys.CERTFILE,
            keyfile=Keys.KEYFILE,
            _run_insecure=False,
        )
        await self.bot.web_manager.start()