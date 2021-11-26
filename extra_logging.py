import asyncio
import logging
import logging.handlers
from queue import SimpleQueue
from typing import List

import aiohttp
import discord
from discord.ext import commands


class DiscordLoggingHandler(logging.Handler):
    """
    A handler class which sends logs to a Discord channel
    """

    def __init__(
        self,
        webhook: str,
        loop: asyncio.AbstractEventLoop = None,
        min_log_level: int = logging.WARNING,
    ):
        super().__init__()
        self._webhook = webhook
        self._loop = loop or asyncio.get_event_loop()
        self._min_log_level = min_log_level

    async def _send_to_webhook(
        self, error_level: int, error_type: str, message: str
    ) -> None:
        # Get a color for the embed
        if error_level < logging.WARNING:
            color = discord.Color.green()
        elif error_level == logging.WARNING:
            color = discord.Color.gold()
        elif error_level > logging.WARNING:
            color = discord.Color.red()

        # Create the embed
        embed = discord.Embed(title=error_type, description=message, color=color)

        # Send the embed
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(
                self._webhook, adapter=discord.AsyncWebhookAdapter(session)
            )
            await webhook.send(embed=embed)

    def emit(self, record: logging.LogRecord) -> None:
        # Only log the message if it's above the minimum level
        if record.levelno >= self._min_log_level:
            # Add a task to send the error to Discord so that we don't stop the event loop
            self._loop.create_task(
                self._send_to_webhook(record.levelno, record.levelname, record.message)
            )
