from dataclasses import dataclass
from logging import Logger
from types import coroutine
from typing import Any, Callable, Coroutine, List

from discord.ext import commands

from layers.business.moderation_bl import ModerationBL

from .time_bl import TimeBL
from .vrc_name_bl import VRChatBL
from .programming_bl import ProgrammingBL
from .web_manager_bl import WebManagerBL


@dataclass
class BusinessLayerWrapper:
    """
    Wrapper class for all the business layer classes.
    """

    time: TimeBL
    vrc: VRChatBL
    p: ProgrammingBL
    web: WebManagerBL
    mod: ModerationBL
