import asyncio
import datetime as dt
import logging
import logging.handlers
import traceback
from queue import SimpleQueue
from typing import List, Optional

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

        ready_embed = discord.Embed(
            title="Discord Logging Online",
            description="From LPD Officer Monitor.",
            color=discord.Color.green(),
            timestamp=dt.datetime.now(tz=dt.timezone.utc),
        )
        self._loop.run_until_complete(self._send_embed(ready_embed))

    async def _send_embed(self, embed: discord.Embed):
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(
                self._webhook, adapter=discord.AsyncWebhookAdapter(session)
            )
            await webhook.send(embed=embed)

    async def _send_to_webhook(
        self,
        error_level: int,
        error_type: str,
        message: str,
        trace: Optional[str] = None,
        filename: Optional[str] = None,
        line_num: Optional[int] = None,
        func_name: Optional[str] = None,
        time: Optional[dt.datetime] = None,
    ) -> None:
        # Get a color for the embed
        if error_level < logging.WARNING:
            color = discord.Color.green()
        elif error_level == logging.WARNING:
            color = discord.Color.gold()
        elif error_level > logging.WARNING:
            color = discord.Color.red()

        # Create the embed
        embed = discord.Embed(
            title=error_type, description=message + "\n\n" + (trace or ""), color=color
        )

        # Add extra fields
        if filename is not None:
            embed.add_field(name="Filename", value=filename)
        if line_num is not None:
            embed.add_field(name="Line Number", value=line_num)
        if func_name is not None:
            embed.add_field(name="Function", value=func_name)
        if time is not None:
            embed.timestamp = time

        await self._send_embed(embed)

    def emit(self, record: logging.LogRecord) -> None:
        # Only log the message if it's above the minimum level
        if record.levelno >= self._min_log_level:

            # Convert date to datetime
            iso_time = ",".join(record.asctime.split(",")[0:-1])
            time = dt.datetime.fromisoformat(iso_time)

            # Add a task to send the error to Discord so that we don't stop the event loop
            # TODO: Account for rate limiting when logging a lot at once
            self._loop.create_task(
                self._send_to_webhook(
                    error_level=record.levelno,
                    error_type=record.levelname,
                    message=record.msg,
                    trace=record.exc_text,
                    filename=record.filename,
                    line_num=record.lineno,
                    func_name=record.funcName,
                    time=time,
                )
            )
