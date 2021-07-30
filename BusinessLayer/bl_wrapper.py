from logging import Logger
from types import coroutine
from typing import Any, Callable, Coroutine, List

from discord.ext import commands

from .time_bl import TimeBL
from .vrc_name_bl import VRChatBL
from .programming_bl import ProgrammingBL
from .web_manager_bl import WebManagerBL


class BusinessLayerWrapper:
    """
    Wrapper class for all the business layer classes.
    """

    def __init__(self, bot: commands.Bot):
        self._time_bl = TimeBL(bot, self)
        self._vrc_bl = VRChatBL()
        self._programming_bl = ProgrammingBL(bot, self)
        self._web_manager_bl = WebManagerBL(bot, self)

        self._all_bl_layers = [self._time_bl, self._vrc_bl, self._programming_bl]

        self._on_ready_events: List[Coroutine] = []

        # Loop through the functions in the above classes and add their methods that don't start with _ to this class
        for bl_layer in self._all_bl_layers:
            for func in dir(bl_layer):
                if not func.startswith("_") and callable(getattr(bl_layer, func)):
                    setattr(self, func, getattr(bl_layer, func))

    def subscribe_on_ready(self, func: Coroutine[Any, Any, Any]) -> None:
        self._on_ready_events.append(func)

    @property
    def on_ready_events(self):
        return self._on_ready_events
