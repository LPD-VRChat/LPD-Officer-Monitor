from src.BusinessLayer.bl_wrapper import BusinessLayerWrapper
from os import listdir
from discord.ext import commands


# Loop through modules at the same level and get their names without a file extention
_modules = [
    module.replace(".py", "")
    for module in listdir(__path__[0])  # type: ignore
    if module.endswith(".py") and not module.startswith("__")
]


def setup(bot: commands.Bot, bl_wrapper: BusinessLayerWrapper):
    bot.bl_wrapper = bl_wrapper

    for module in _modules:
        bot.load_extension(__loader__.name + "." + module)  # type: ignore

    # Remove the reference to the bl_wrapper from the bot to make sure it isn't interfaced with from the wrong places
    del bot.bl_wrapper
