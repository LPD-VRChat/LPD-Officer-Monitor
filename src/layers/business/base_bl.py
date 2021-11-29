# Standard
from __future__ import annotations
from typing import Callable, Optional, TYPE_CHECKING
import asyncio

# Community
from discord.ext import commands

# Custom
if TYPE_CHECKING:
    from . import BusinessLayerWrapper


class DiscordListenerBL:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        # Loop through all methods and add them as an event to the bot if they have a discord_event property
        for attr in dir(self):
            func = getattr(self, attr)
            if callable(func) and hasattr(func, "discord_event"):
                self.bot.add_listener(func, func.discord_event)


def bl_listen(name: Optional[str] = None):
    """
    A function that returns a decorator for a method in a business layer class
    to register it as an event with the bot.
    """

    def decorator(func: Callable):

        # Make sure the func is a coroutine
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f"{func} is not a coroutine")

        async def wrapper(self, *args, **kwargs):
            return await func(self, *args, **kwargs)

        # Keep the same name/doc string on the function
        if func.__name__.startswith("_"):
            wrapper.__name__ = func.__name__
        else:
            wrapper.__name__ = f"_{func.__name__}"
        wrapper.__doc__ = func.__doc__

        # Store the discord event on the function so that it can
        # be picked upon class initialization
        wrapper.discord_event = name or func.__name__  # type: ignore

        return wrapper

    return decorator
