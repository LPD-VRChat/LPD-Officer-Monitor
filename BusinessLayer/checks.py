# Community
from discord.ext import commands

# Mine
import discord.errors as errors


def template_check():
    def predicate(ctx):
        officer = True
        if officer:
            return True
        else:
            raise errors.Forbidden()

    return commands.check(predicate)
