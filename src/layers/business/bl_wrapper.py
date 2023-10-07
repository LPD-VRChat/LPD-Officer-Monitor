from dataclasses import dataclass
from logging import Logger
from types import coroutine
from typing import Any, Callable, Coroutine, List

from discord.ext import commands

from src.layers.business.moderation_bl import ModerationBL

from .modules.mm_bl import MemberManagementBL
from .modules.pt_bl import PatrolTimeBL
from .modules.loa_bl import MemberActivityBL
from .vrc_name_bl import VRChatBL
from .programming_bl import ProgrammingBL
from .web_manager_bl import WebManagerBL


@dataclass
class BusinessLayerWrapper:
    """
    Wrapper class for all the business layer classes.
    """

    mm_bl: MemberManagementBL
    pt_bl: PatrolTimeBL
    loa_bl: MemberActivityBL
    vrc: VRChatBL
    p: ProgrammingBL
    web: WebManagerBL
    mod: ModerationBL


def create(bot) -> BusinessLayerWrapper:
    return BusinessLayerWrapper(
        MemberManagementBL(bot),
        PatrolTimeBL(bot),
        MemberActivityBL(bot),
        VRChatBL(bot),
        ProgrammingBL(bot),
        WebManagerBL(bot),
        ModerationBL(bot),
    )


def destroy(blwrp: BusinessLayerWrapper):
    blwrp.mm_bl.remove_listener()
    blwrp.pt_bl.remove_listener()
    blwrp.loa_bl.remove_listener()
    # blwrp.vrc.remove_listener()
    blwrp.p.remove_listener()
    blwrp.pt_bl.remove_listener()
    blwrp.mod.remove_listener()
    # we cannot nullify bot because some task are queued and will execute after the reload
    # blwrp.mm_bl.bot = None
    # blwrp.pt_bl.bot = None
    # blwrp.loa_bl.bot = None
    # blwrp.p.bot = None
    # blwrp.pt_bl.bot = None
    # blwrp.mod.bot = None

    blwrp.mm_bl = None
    blwrp.pt_bl = None
    blwrp.loa_bl = None
    blwrp.p = None  # type: ignore
    blwrp.pt_bl = None
    blwrp.mod = None
