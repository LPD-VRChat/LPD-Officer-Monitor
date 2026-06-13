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
    Dict,
)
import asyncio
from dataclasses import dataclass
import logging

# Community
from discord.ext import commands
import discord

# Custom
if TYPE_CHECKING:
    from . import BusinessLayerWrapper
from src.layers.storage.models import Officer

log = logging.getLogger("lpd-officer-monitor")


class EventSenderMixin:

    # Static subscribers dictionary shared across all instances
    __subscribers: Dict[type, List[Callable]] = {}
    # Static lock for thread-safe access, probably not safe enough because only used turing event notifications
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self) -> None:
        super().__init__()

        self._own_subscribers: List[tuple[type, Callable]] = []

        for attr in dir(self):
            func = getattr(self, attr)
            if callable(func) and hasattr(func, "subscribed_event_type"):
                event_type = func.subscribed_event_type  # type: ignore
                self.subscribe(event_type, func)

    def subscribe(self, event_type: type, subscriber: Callable[[Any], Any]):
        """
        Subscribe to an event using type.
        Only for Business layer!!!
        """
        if event_type not in self.__subscribers:
            self.__subscribers[event_type] = []
        self.__subscribers[event_type].append(subscriber)
        self._own_subscribers.append((event_type, subscriber))

    def remove_business_listeners(self) -> None:
        for event_type, subscriber in self._own_subscribers:
            if event_type in self.__subscribers:
                try:
                    self.__subscribers[event_type].remove(subscriber)
                    if not self.__subscribers[event_type]:
                        del self.__subscribers[event_type]
                except ValueError:
                    pass

    async def _notify_all(self, data: Any) -> None:
        """
        Notify all listeners of this class for the specific event type and if the listeners are async
        functions run them asynchronously in the background.
        Uses a static lock to ensure thread-safe access.
        """
        event_type = type(data)

        if self._lock.locked():
            log.warning(
                f"EventSenderMixin._lock is locked, {self.__class__.__name__} is trying to notify all listeners of {event_type}"
            )

        async with self._lock:
            subscribers = self.__subscribers.get(event_type, []).copy()

            for subscriber in subscribers:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(data)
                else:
                    subscriber(data)


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
    # TODO: rename this to discord, those are not originating from the business layer

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


def business_event(event_type: type):
    """
    A decorator for methos to subscribe to events in a class that inherits from EventSenderMixin.

    Usage:
        @business_event(MemberManagementEvent.MemberJoined)
        def on_member_joined(self, event: MemberManagementEvent.MemberJoined):
            ...
    """

    def decorator(func: Callable):
        # Store the event type on the function so that it can
        # be picked up during class initialization
        func.subscribed_event_type = event_type  # type: ignore

        # Keep the same name/doc string on the function
        return func

    return decorator


########################################################
# Event types for the business layer
########################################################

# Declared here to avoir circular imports


class MemberManagementEvent:
    @dataclass
    class MemberJoined:
        officer: Officer
        member: discord.Member

    @dataclass
    class MemberJoinedAfterMaxWait:
        # TODO: should be an enum in the normal Joined
        officer: Officer
        member: discord.Member

    @dataclass
    class MemberLeft:
        member_id: int
        member: Optional[discord.Member]
        reason: str = "unknown"
        officer: Optional[Officer] = None
