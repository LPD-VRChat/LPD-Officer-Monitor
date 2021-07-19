from os import listdir
from discord.ext import commands
from importlib import import_module

# Loop through modules at the same level and get their names without a file extention
_modules = [
    module.replace(".py", "")
    for module in listdir(__path__[0])  # type: ignore
    if module.endswith(".py") and not module.startswith("__")
]


def setup(bot: commands.Bot):
    for module_name in _modules:
        module = import_module("." + module_name, package="BusinessLayer.DiscordChecks")
        function = getattr(module, "_" + module_name)
        bot.check(function(bot))
