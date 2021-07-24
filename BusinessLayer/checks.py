import Settings

# Community
from discord.ext import commands

# Mine
import discord.errors as errors
from BusinessLayer.extra_functions import has_role_id


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
        return has_role_id(ctx.author, Settings.PROGRAMMING_TEAM_ROLE)

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
            or ctx.channel.id == Settings.ADMIN_BOT_CHANNEL
        )  # This is for now, but later we'll need to write this correctly

    return commands.check(predicate)


def is_general_bot_channel():
    def predicate(ctx):
        return (
            ctx.channel.id == Settings.GENERAL_BOT_CHANNEL
            or ctx.channel.id == Settings.ADMIN_BOT_CHANNEL
            or ctx.channel.id == Settings.TEAM_BOT_CHANNEL
        )  # This is for now, but later we'll need to write this correctly

    return commands.check(predicate)


def is_chat_moderator():
    def predicate(ctx):
        return has_role_id(ctx.author, Settings.CHAT_MODERATOR_ROLE) or has_role_id(
            ctx.author, Settings.MODERATOR_ROLE
        )

    return commands.check(predicate)


def is_moderator():
    def predicate(ctx):
        return has_role_id(ctx.author, Settings.MODERATOR_ROLE)

    return commands.check(predicate)


def is_team_lead():
    def predicate(ctx):
        return has_role_id(ctx.author, Settings.TEAM_LEAD_ROLE)

    return commands.check(predicate)


def is_dev_team():
    def predicate(ctx):
        return has_role_id(ctx.author, Settings.DEV_TEAM_ROLE)

    return commands.check(predicate)


def is_white_shirt():
    def predicate(ctx):
        for Rank in Settings.ROLE_LADDER.__dict__.values():
            if has_role_id(ctx.author, Rank.id) and Rank.is_white_shirt:
                return True
        return False

    return commands.check(predicate)


def is_admin():
    def predicate(ctx):
        for Rank in Settings.ROLE_LADDER.__dict__.values():
            if has_role_id(ctx.author, Rank.id) and Rank.is_admin:
                return True
        return False

    return commands.check(predicate)