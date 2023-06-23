from re import L
import settings

from typing import Callable, TypeVar

T = TypeVar("T")

# Community
from discord.ext import commands
import discord

# Custom
import discord.errors as errors
from src.layers.business.extra_functions import has_role_id, is_lpd_member


def template_check(slash_cmd=False):
    officer = True

    def predicate(ctx):
        if officer:
            return True
        else:
            raise errors.Forbidden()

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        return officer

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def is_programming_team(slash_cmd=False):
    def predicate(ctx):
        return has_role_id(ctx.author, settings.PROGRAMMING_TEAM_ROLE)

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        return has_role_id(interaction.user, settings.PROGRAMMING_TEAM_ROLE)

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def is_admin_bot_channel(slash_cmd=False):
    def predicate(ctx):
        return ctx.channel.id == settings.ADMIN_BOT_CHANNEL

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        return interaction.channel_id == settings.ADMIN_BOT_CHANNEL

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def is_recruiter_bot_channel(slash_cmd=False):
    def predicate(ctx):
        return ctx.channel.id == settings.RECRUITER_BOT_CHANNEL

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        return interaction.channel_id == settings.RECRUITER_BOT_CHANNEL

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def is_team_bot_channel(slash_cmd=False):
    def predicate(ctx):
        return ctx.channel.id in [
            settings.TEAM_BOT_CHANNEL,
            settings.ADMIN_BOT_CHANNEL,
            settings.APPLICATION_CHANNEL,
        ]

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        return interaction.channel_id in [
            settings.TEAM_BOT_CHANNEL,
            settings.ADMIN_BOT_CHANNEL,
            settings.APPLICATION_CHANNEL,
        ]

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def is_general_bot_channel(slash_cmd=False):
    def predicate(ctx):
        return ctx.channel.id in [
            settings.GENERAL_BOT_CHANNEL,
            settings.ADMIN_BOT_CHANNEL,
            settings.TEAM_BOT_CHANNEL,
            settings.APPLICATION_CHANNEL,
        ]

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        return interaction.channel_id in [
            settings.GENERAL_BOT_CHANNEL,
            settings.ADMIN_BOT_CHANNEL,
            settings.TEAM_BOT_CHANNEL,
            settings.APPLICATION_CHANNEL,
        ]

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def is_chat_moderator(slash_cmd=False):
    def predicate(ctx):
        return has_role_id(ctx.author, settings.CHAT_MODERATOR_ROLE) or (
            has_role_id(ctx.author, settings.MODERATOR_ROLE)
        )

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        return has_role_id(interaction.user, settings.CHAT_MODERATOR_ROLE) or (
            has_role_id(interaction.user, settings.MODERATOR_ROLE)
        )

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def is_moderator(slash_cmd=False):
    def predicate(ctx):
        return has_role_id(ctx.author, settings.MODERATOR_ROLE)

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        return has_role_id(interaction.user, settings.MODERATOR_ROLE)

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def is_team_lead(slash_cmd=False):
    def predicate(ctx):
        return has_role_id(ctx.author, settings.TEAM_LEAD_ROLE)

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        return has_role_id(interaction.user, settings.TEAM_LEAD_ROLE)

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def is_dev_team(slash_cmd=False):
    def predicate(ctx):
        return has_role_id(ctx.author, settings.DEV_TEAM_ROLE)

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        return has_role_id(interaction.user, settings.DEV_TEAM_ROLE)

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def is_white_shirt(slash_cmd=False):
    def predicate(ctx):
        for rank in settings.ROLE_LADDER.__dict__.values():
            if has_role_id(ctx.author, rank.id) and rank.is_white_shirt:
                return True
        return False

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        for rank in settings.ROLE_LADDER.__dict__.values():
            if has_role_id(interaction.user, rank.id) and rank.is_white_shirt:
                return True
        return False

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def is_admin(slash_cmd=False):
    def predicate(ctx):
        for rank in settings.ROLE_LADDER.__dict__.values():
            rank = rank.value
            if has_role_id(ctx.author, rank.id) and rank.is_admin:
                return True
        return False

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        for rank in settings.ROLE_LADDER.__dict__.values():
            if has_role_id(interaction.user, rank.id) and rank.is_admin:
                return True
        return False

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def is_any_trainer(slash_cmd=False):
    def predicate(ctx):
        if [
            role
            for role in ctx.author.roles
            if role.id in settings.TRAINER_TEAMS.values()
        ] != []:
            return True
        return False

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        if isinstance(interaction.user, discord.User):
            raise errors.InvalidData("cannot get roles on `User`")
        if [
            role
            for role in interaction.user.roles
            if role.id in settings.TRAINER_TEAMS.values()
        ] != []:
            return True
        return False

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def is_event_host(slash_cmd=False):
    def predicate(ctx):
        return has_role_id(ctx.author, settings.EVENT_HOST_ROLE)

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        return has_role_id(interaction.user, settings.EVENT_HOST_ROLE)

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def is_recruiter(slash_cmd=False):
    def predicate(ctx):
        return has_role_id(ctx.author, settings.RECRUITER_ROLE)

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        return has_role_id(interaction.user, settings.RECRUITER_ROLE)

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def is_officer(slash_cmd=False):
    def predicate(ctx):
        return is_lpd_member(ctx.author)

    def predicate_interaction(interaction: discord.Interaction) -> bool:
        return is_lpd_member(interaction.user)

    if slash_cmd:
        return discord.app_commands.check(predicate_interaction)
    else:
        return commands.check(predicate)


def app_cmd_check_any(*checks: Callable[[T], T]) -> Callable[[T], T]:
    """logical or for app_command

    super hacky code, may break when updating discord library
    """

    # there is no easy way to det the predicate for app_cmd checks
    # so we hack around and create a fake command where all the checks gets added to
    def fake_command():
        pass

    fake_func = fake_command
    for wrapped in checks:
        fake_func = wrapped(fake_func)

    async def predicate(interaction: discord.Interaction) -> bool:
        for check in fake_func.__discord_app_commands_checks__:
            try:
                value = await discord.utils.maybe_coroutine(check, interaction)
                if value:
                    return True  # optimization: early out at first allowed
            except discord.app_commands.AppCommandError:
                continue
            except:
                continue
                import traceback

                print("".join(traceback.format_exc()))
        else:
            return False

    # TODO we could add some metadata maybe when we create the check
    return discord.app_commands.check(predicate)
