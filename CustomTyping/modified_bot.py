# Standard
from typing import Any, Dict, TYPE_CHECKING

# Community
from discord.ext import commands

# Custom
if TYPE_CHECKING:
    from Classes.OfficerManager import OfficerManager
    from Classes.VRChatUserManager import VRChatUserManager
    from Classes.SQLManager import SQLManager


class Bot(commands.Bot):
    def __init__(self):
        self.officer_manager: OfficerManager = None  # type: ignore
        self.user_manager: VRChatUserManager = None  # type: ignore
        self.sql: SQLManager = None  # type: ignore
        self.settings: Dict[str, Any] = None  # type: ignore
        self.everything_ready: bool = None  # type: ignore

        # Make sure this class doesn't get instantiated
        raise NotImplementedError(
            "The bot class from modified_bot should not be instantiated and is only for typing."
        )
