# Standard
from __future__ import annotations
from typing import (
    Any,
    Callable,
    Generic,
    List,
    Literal,
    Optional,
    TYPE_CHECKING,
    TypeVar,
)
import asyncio

# Community
from discord.ext import commands

# Custom
if TYPE_CHECKING:
    from . import BusinessLayerWrapper


ESM_DATA_T = TypeVar("ESM_DATA_T")


class EventSenderMixin(Generic[ESM_DATA_T]):
    """
    Easily allow this class to be listended to and send events without any
    boilerplate.
    """

    def __init__(self) -> None:
        super().__init__()

        self.__subscribers: list[Callable] = []

    def subscribe(self, subscriber: Callable[[ESM_DATA_T], Any]):
        """
        Ask for a function to be called each time this class fires an event.
        The subscriber can be either a regular function or an async function
        and class will handle that logic for you and call either properly.
        """
        self.__subscribers.append(subscriber)

    def _notify_all(self, data: ESM_DATA_T) -> None:
        """
        Notify all listiners of this class and if the listiners are async
        functions run them asynchronously in the background.
        """
        loop = asyncio.get_event_loop()

        # Call all the subscribers
        for subscriber in self.__subscribers:
            return_val = subscriber(data)

            # Start it if the return value was a not-yet run coroutine
            if asyncio.iscoroutine(return_val):
                loop.create_task(return_val)


class DiscordListenerMixin:
    def __init__(self) -> None:
        super().__init__()

        # Make sure this class has the required bot on it
        assert getattr(self, "bot", None) is not None
        assert isinstance(self.bot, commands.Bot)  # type: ignore

        # Loop through all methods and add them as an event to the bot if they have a discord_event property
        for attr in dir(self):
            func = getattr(self, attr)
            if callable(func) and hasattr(func, "discord_event"):
                self.bot.add_listener(func, func.discord_event)  # type: ignore

    def remove_listener(self):
        # not using __del__ as some copies are left behind
        # Loop through all methods and add them as an event to the bot if they have a discord_event property
        for attr in dir(self):
            func = getattr(self, attr)
            if callable(func) and hasattr(func, "discord_event"):
                self.bot.remove_listener(func, func.discord_event)  # type: ignore


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
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        # for debug purpuse
        wrapper.__orginal_module__ = func.__module__  # type: ignore
        wrapper.__orginal_qualname__ = func.__qualname__  # type: ignore
        # Store the discord event on the function so that it can
        # be picked upon class initialization
        wrapper.discord_event = name or func.__name__  # type: ignore

        return wrapper

    return decorator
