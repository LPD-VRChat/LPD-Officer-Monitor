from re import L
import settings

# Community
from discord.ext import commands

# Custom
import discord.errors as errors
from src.layers.business.extra_functions import has_role_id


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
        return has_role_id(ctx.author, settings.PROGRAMMING_TEAM_ROLE)

    return commands.check(predicate)


def is_admin_bot_channel():
    def predicate(ctx):
        return (
            ctx.channel.id == settings.ADMIN_BOT_CHANNEL
        )  # This is for now, but later we'll need to write this correctly

    return commands.check(predicate)


def is_team_bot_channel():
    def predicate(ctx):
        return ctx.channel.id in [
            settings.TEAM_BOT_CHANNEL,
            settings.ADMIN_BOT_CHANNEL,
        ]  # This is for now, but later we'll need to write this correctly

    return commands.check(predicate)


def is_general_bot_channel():
    def predicate(ctx):
        return ctx.channel.id in [
            settings.GENERAL_BOT_CHANNEL,
            settings.ADMIN_BOT_CHANNEL,
            settings.TEAM_BOT_CHANNEL,
        ]  # This is for now, but later we'll need to write this correctly

    return commands.check(predicate)


def is_chat_moderator():
    def predicate(ctx):
        return has_role_id(ctx.author, settings.CHAT_MODERATOR_ROLE) or (
            has_role_id(ctx.author, settings.MODERATOR_ROLE)
        )

    return commands.check(predicate)


def is_moderator():
    def predicate(ctx):
        return has_role_id(ctx.author, settings.MODERATOR_ROLE)

    return commands.check(predicate)


def is_team_lead():
    def predicate(ctx):
        return has_role_id(ctx.author, settings.TEAM_LEAD_ROLE)

    return commands.check(predicate)


def is_dev_team():
    def predicate(ctx):
        return has_role_id(ctx.author, settings.DEV_TEAM_ROLE)

    return commands.check(predicate)


def is_white_shirt():
    def predicate(ctx):
        for rank in settings.ROLE_LADDER.__dict__.values():
            if has_role_id(ctx.author, rank.id) and rank.is_white_shirt:
                return True
        return False

    return commands.check(predicate)


def is_admin():
    def predicate(ctx):
        for rank in settings.ROLE_LADDER.__dict__.values():
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
            if role.id in settings.TRAINER_TEAMS.values()
        ] != []:
            return True
        return False

    return commands.check(predicate)


def is_event_host():
    def predicate(ctx):
        if has_role_id(ctx.author, settings.EVENT_HOST_ROLE):
            return True
        return False

    return commands.check(predicate)
