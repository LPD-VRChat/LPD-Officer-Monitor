from itertools import count
from dataclasses import dataclass, field

position_counter = count(0)


@dataclass
class RoleLadderElement:
    name: str
    name_id: str
    id: int
    is_detainable: bool = True
    is_white_shirt: bool = False
    is_admin: bool = False
    position: int = field(
        init=False, default_factory=lambda: next(position_counter)
    )

    def as_discord_role(self, bot):
        """Returns the discord.Role object for this role ladder element"""
        return bot.get_role(self.id)


@dataclass
class RoleLadder:
    cadet: RoleLadderElement
    recruit: RoleLadderElement
    officer: RoleLadderElement
    senior_officer: RoleLadderElement
    corporal: RoleLadderElement
    sergeant: RoleLadderElement
    staff_sergeant: RoleLadderElement
    lieutenant: RoleLadderElement
    advisor: RoleLadderElement
    captain: RoleLadderElement
    deputy_chief: RoleLadderElement
    chief: RoleLadderElement
