from logging import Logger

from discord.ext import commands

from .time_bl import TimeBL
from .vrc_name_bl import VRChatBL
from .programming_bl import ProgrammingBL


class BusinessLayerWrapper:
    """
    Wrapper class for all the business layer classes.
    """

    def __init__(self, bot: commands.Bot):
        self._time_bl = TimeBL()
        self._vrc_bl = VRChatBL()
        self._programming_bl = ProgrammingBL(bot, self)

        self._all_bl_layers = [self._time_bl, self._vrc_bl, self._programming_bl]

        # Loop through the functions in the above classes and add their methods that don't start with _ to this class
        for bl_layer in self._all_bl_layers:
            for func in dir(bl_layer):
                if not func.startswith("_") and callable(getattr(bl_layer, func)):
                    setattr(self, func, getattr(bl_layer, func))
