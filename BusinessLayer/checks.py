import Settings

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


def is_programming_team():
    def predicate(ctx):
        return (
            True
        )  # This is for now, but later we'll need to check if the user is in the programming team

    return commands.check(predicate)


def is_admin_bot_channel():
    def predicate(ctx):
        return (
            ctx.channel.id == Settings.ADMIN_BOT_CHANNEL
        )  # This is for now, but later we'll need to write this correctly

    return commands.check(predicate)


def is_team_bot_channel():
    def predicate(ctx):
        return (
            ctx.channel.id == Settings.TEAM_BOT_CHANNEL
        )  # This is for now, but later we'll need to write this correctly

    return commands.check(predicate)


def is_general_bot_channel():
    def predicate(ctx):
        return (
            ctx.channel.id == Settings.GENERAL_BOT_CHANNEL
        )  # This is for now, but later we'll need to write this correctly

    return commands.check(predicate)

