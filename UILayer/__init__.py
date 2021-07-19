from . import DiscordCommands
from os import listdir


def import_from(module, name):
    module = __import__(module, fromlist=[name])
    return getattr(module, name)


modules = [
    module.split(".")[0]
    for module in listdir(DiscordCommands.__path__._path[0])
    if module[0] == module[0].upper() and module.endswith(".py")
]
cogs = []
for module in modules:
    cog = import_from("UILayer.DiscordCommands." + module, module)
    cogs.append(cog)
