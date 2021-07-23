import os as _os
from itertools import count


class role_ladder_element:
    position_counter = count(0)

    def __init__(
        self,
        name: str,
        name_id: str,
        id: int,
        is_detainable: bool = True,
        is_white_shirt: bool = False,
        is_admin: bool = False,
    ):

        self.name = name
        self.name_id = name_id
        self.id = id
        self.is_detainable = is_detainable
        self.is_white_shirt = is_white_shirt
        self.is_admin = is_admin
        self.position = next(self.position_counter)

    @property
    def role(self, bot):
        """Returns the discord.Role object for this role ladder element"""
        return bot.get_role(self.id)


try:
    if _os.environ.get("LPD_OFFICER_MONITOR_ENVIRONMENT") == "dev":
        from .dev import *
    else:
        from .production import *
except ImportError:
    pass

try:
    from .local import *
except ImportError:
    pass
