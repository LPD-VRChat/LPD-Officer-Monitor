from dataclasses import dataclass
from logging import Logger
from types import coroutine
from typing import Any, Callable, Coroutine, List

from discord.ext import commands

from src.layers.business.moderation_bl import ModerationBL

from .modules.mm_bl import MemberManagementBL
from .vrc_name_bl import VRChatBL
from .programming_bl import ProgrammingBL
from .web_manager_bl import WebManagerBL


@dataclass
class BusinessLayerWrapper:
    """
    Wrapper class for all the business layer classes.
    """

    mm_bl: MemberManagementBL
    vrc: VRChatBL
    p: ProgrammingBL
    web: WebManagerBL
    mod: ModerationBL
