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

    def __init__(self, bot: commands.Bot, business_layers: List[Any]):
        self._all_layers = business_layers
        self._on_ready_events: List[Coroutine] = []

        # Loop through the functions in the above classes and add their methods that don't start with _ to this class
        for business_layer in self._all_layers:
            for func in dir(business_layer):
                if not func.startswith("_") and callable(getattr(business_layer, func)):
                    setattr(self, func, getattr(business_layer, func))

    def subscribe_on_ready(self, func: Coroutine[Any, Any, Any]) -> None:
        self._on_ready_events.append(func)

    @property
    def on_ready_events(self):
        return self._on_ready_events
