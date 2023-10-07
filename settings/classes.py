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
    position: int = field(init=False, default_factory=lambda: next(position_counter))

    def as_discord_role(self, bot):
        """Returns the discord.Role object for this role ladder element"""
        return bot.guild.get_role(self.id)

    def _check_type(self, a):
        if not isinstance(a, RoleLadderElement):
            raise ValueError(
                f"Cannot compare other type ({type(a)}) to RoleLadderElement"
            )

    def __lt__(self, other):  # less-than (<)
        self._check_type(other)
        return self.position < other.position

    def __le__(self, other):  # less-than or equal to (<=)
        self._check_type(other)
        return self.position <= other.position

    def __eq__(self, other):  # equal (==)
        self._check_type(other)
        return self.position == other.position and self.id == other.id

    def __ne__(self, other):  # not equal (!=)
        self._check_type(other)
        return self.position != other.position and self.id != other.id

    def __gt__(self, other):  # the greater-than (>)
        self._check_type(other)
        return self.position > other.position

    def __ge__(self, other):  # greater-than or equal to (>=)
        self._check_type(other)
        return self.position >= other.position


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

    def items(self):
        return self.__dict__.items()
