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

    def __init__(self, bot: commands.Bot, **kwargs):
        self._layers = kwargs

    def clean_shutdown(
        self,
        location: str = "the console",
        shutdown_by: str = "KeyboardInterrupt",
        exit: bool = True,
    ):
        return self._layers["p_bl"].clean_shutdown(location, shutdown_by, exit)
