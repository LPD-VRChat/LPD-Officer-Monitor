# Standard
from typing import Any, Dict

# Community
from discord.ext import commands

# Custom
from Classes.OfficerManager import OfficerManager
from Classes.SQLManager import SQLManager
from Classes.VRChatUserManager import VRChatUserManager

class Bot(commands.Bot):
    officer_manager: OfficerManager
    user_manager: VRChatUserManager
    sql: SQLManager
    settings: Dict[str, Any]
    everything_ready: bool
