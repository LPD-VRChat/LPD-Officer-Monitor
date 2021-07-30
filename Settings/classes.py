from itertools import count
from dataclasses import dataclass


class RoleLadderElement:
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

    def as_discord_role(self, bot):
        """Returns the discord.Role object for this role ladder element"""
        return bot.get_role(self.id)


class RoleLadder:

    cadet: RoleLadderElement = None
    recruit: RoleLadderElement = None
    officer: RoleLadderElement = None
    senior_officer: RoleLadderElement = None
    corporal: RoleLadderElement = None
    sergeant: RoleLadderElement = None
    staff_sergeant: RoleLadderElement = None
    lieutenant: RoleLadderElement = None
    advisor: RoleLadderElement = None
    captain: RoleLadderElement = None
    deputy_chief: RoleLadderElement = None
    chief: RoleLadderElement = None