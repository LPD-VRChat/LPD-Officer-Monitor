import asyncio
import logging
import logging.handlers
from queue import SimpleQueue
from typing import List

import discord
from discord.ext import commands


class LocalQueueHandler(logging.handlers.QueueHandler):
    def emit(self, record: logging.LogRecord) -> None:
        # Removed the call to self.prepare(), handle task cancellation
        try:
            self.enqueue(record)
        except asyncio.CancelledError:
            raise
        except Exception:
            self.handleError(record)


def setup_logging_queue() -> None:
    """Move log handlers to a separate thread.

    Replace handlers on the root logger with a LocalQueueHandler,
    and start a logging.QueueListener holding the original
    handlers.

    """
    queue: SimpleQueue = SimpleQueue()
    root = logging.getLogger()

    handlers: List[logging.Handler] = []

    handler = LocalQueueHandler(queue)
    root.addHandler(handler)
    for h in root.handlers[:]:
        if h is not handler:
            root.removeHandler(h)
            handlers.append(h)

    listener = logging.handlers.QueueListener(
        queue, *handlers, respect_handler_level=True
    )
    listener.start()


class DiscordLoggingHandler(logging.Handler):
    """
    A handler class which sends logs to a Discord channel
    """

    def __init__(
        self,
        bot: commands.Bot,
        channel_id: int,
        loop: asyncio.AbstractEventLoop = None,
        min_log_level: int = logging.WARNING,
    ):
        super().__init__()
        self._bot = bot
        self._channel_id = channel_id
        self._loop = loop or asyncio.get_event_loop()
        self._min_log_level = min_log_level

    def emit(self, record: logging.LogRecord) -> None:
        # Only log the message if it's above the minimum level
        if record.levelno >= self._min_log_level:
            try:
                # Only log the message if the channel is found
                channel: discord.TextChannel = self._bot.get_channel(self._channel_id)
                if channel is None:
                    return

                msg = self.format(record)
                self._loop.run_until_complete(channel.send(msg))
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                self.handleError(record)
