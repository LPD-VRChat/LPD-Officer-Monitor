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
        min_log_level: int = logging.INFO,
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
        self._loop.run_until_complete(self._send(embed=ready_embed))

    async def _send(
        self,
        content: str = discord.utils.MISSING,
        embed: discord.Embed = discord.utils.MISSING,
    ):
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(self._webhook, session=session)
            await webhook.send(content=content, embed=embed)

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
        if error_level < logging.ERROR:
            match (error_level):
                case logging.DEBUG:
                    level_str = ":bug:"
                case logging.INFO:
                    level_str = ":information_source:"
                case logging.WARNING:
                    level_str = ":warning:"
                case logging.ERROR:
                    level_str = ":red_circle:"
                case logging.CRITICAL:
                    level_str = ":octagonal_sign:"
                case _:
                    level_str = ":interrobang:"
            await self._send(
                content=f"{level_str}`{filename.split('.py')[0]}` {message}"
            )
        else:
            # Get a color for the embed
            if error_level == logging.WARNING:
                color = discord.Color.gold()
            elif error_level > logging.WARNING:
                color = discord.Color.red()

            # Create the embed
            embed = discord.Embed(
                title=error_type,
                description=message + "\n\n" + (trace or ""),
                color=color,
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

            await self._send(embed=embed)

    def emit(self, record: logging.LogRecord) -> None:
        # Only log the message if it's above the minimum level
        if record.levelno >= self._min_log_level:
            # Convert date to datetime
            iso_time = ",".join(record.asctime.split(",")[0:-1])
            try:
                time = dt.datetime.fromisoformat(iso_time)
            except ValueError:
                time = dt.datetime.now()

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
