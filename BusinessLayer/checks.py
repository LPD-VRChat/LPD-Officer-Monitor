from re import L
import Settings

# Community
from discord.ext import commands

# Custom
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
        return ctx.channel.id in [
            Settings.TEAM_BOT_CHANNEL,
            Settings.ADMIN_BOT_CHANNEL,
        ]  # This is for now, but later we'll need to write this correctly

    return commands.check(predicate)


def is_general_bot_channel():
    def predicate(ctx):
        return ctx.channel.id in [
            Settings.GENERAL_BOT_CHANNEL,
            Settings.ADMIN_BOT_CHANNEL,
            Settings.TEAM_BOT_CHANNEL,
        ]  # This is for now, but later we'll need to write this correctly

    return commands.check(predicate)


def is_chat_moderator():
    def predicate(ctx):
        return has_role_id(ctx.author, Settings.CHAT_MODERATOR_ROLE) or (
            has_role_id(ctx.author, Settings.MODERATOR_ROLE)
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
        for rank in Settings.ROLE_LADDER:
            rank = rank.value
            if has_role_id(ctx.author, rank.id) and rank.is_white_shirt:
                return True
        return False

    return commands.check(predicate)


def is_admin():
    def predicate(ctx):
        for rank in Settings.ROLE_LADDER:
            rank = rank.value
            if has_role_id(ctx.author, rank.id) and rank.is_admin:
                return True
        return False

    return commands.check(predicate)


def is_any_trainer():
    def predicate(ctx):
        if [
            role
            for role in ctx.author.roles
            if role.id in Settings.TRAINER_TEAMS.values()
        ] != []:
            return True
        return False

    return commands.check(predicate)


def is_event_host():
    def predicate(ctx):
        if has_role_id(ctx.author, Settings.EVENT_HOST_ROLE):
            return True
        return False

    return commands.check(predicate)
