from os import listdir
from discord.ext import commands


# Loop through modules at the same level and get their names without a file extention
_modules = [
    module.replace(".py", "")
    for module in listdir(__path__[0])  # type: ignore
    if module.endswith(".py") and not module.startswith("__")
]


def setup(bot: commands.Bot):
    for module in _modules:
        bot.load_extension(__loader__.name + "." + module)  # type: ignore
