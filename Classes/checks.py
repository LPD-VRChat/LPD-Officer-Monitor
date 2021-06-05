# Community
from discord.ext import commands

# Mine
import Classes.errors as errors


def is_lpd():
    def predicate(ctx):
        officer = ctx.bot.officer_manager.get_officer(ctx.author.id)
        if officer:
            return True
        else:
            raise errors.NotForYouError("This command is only for LPD Members.")

    return commands.check(predicate)


def is_white_shirt():
    def predicate(ctx):
        officer = ctx.bot.officer_manager.get_officer(ctx.author.id)
        if officer and officer.is_white_shirt:
            return True
        else:
            raise errors.NotForYouError("This command is only for LPD White Shirts.")

    return commands.check(predicate)


def is_admin():
    def predicate(ctx):
        officer = ctx.bot.officer_manager.get_officer(ctx.author.id)
        if officer and officer.is_admin:
            return True
        else:
            raise errors.NotForYouError("This command is only for LPD Chiefs.")

    return commands.check(predicate)


def is_admin_bot_channel():
    def predicate(ctx):
        admin_bot_channel = ctx.bot.officer_manager.guild.get_channel(
            ctx.bot.settings["admin_bot_channel"]
        )
        if ctx.message.channel.id != admin_bot_channel.id:
            raise errors.WrongChannelError(
                f"This command only works in {admin_bot_channel.mention}."
            )
        return True

    return commands.check(predicate)


def is_general_bot_channel():
    def predicate(ctx):
        admin_bot_channel = ctx.bot.officer_manager.guild.get_channel(
            ctx.bot.settings["admin_bot_channel"]
        )
        general_bot_channel = ctx.bot.officer_manager.guild.get_channel(
            ctx.bot.settings["general_bot_channel"]
        )
        if (
            ctx.message.channel.id != admin_bot_channel.id
            and ctx.message.channel.id != general_bot_channel.id
        ):
            raise errors.WrongChannelError(
                f"This command only works in {general_bot_channel.mention} or {admin_bot_channel.mention}."
            )
        return True

    return commands.check(predicate)


def is_application_channel():
    def predicate(ctx):
        admin_bot_channel = ctx.bot.officer_manager.guild.get_channel(
            ctx.bot.settings["admin_bot_channel"]
        )
        application_channel = ctx.bot.officer_manager.guild.get_channel(
            ctx.bot.settings["application_channel"]
        )
        if (
            ctx.message.channel.id != admin_bot_channel.id
            and ctx.message.channel.id != application_channel.id
        ):
            raise errors.WrongChannelError(
                f"This command only works in {application_channel.mention} or {admin_bot_channel.mention}."
            )
        return True

    return commands.check(predicate)


def is_team_bot_channel():
    def predicate(ctx):
        admin_bot_channel = ctx.bot.officer_manager.guild.get_channel(
            ctx.bot.settings["admin_bot_channel"]
        )
        team_bot_channel = ctx.bot.officer_manager.guild.get_channel(
            ctx.bot.settings["team_bot_channel"]
        )
        if (
            ctx.message.channel.id != admin_bot_channel.id
            and ctx.message.channel.id != team_bot_channel.id
        ):
            raise errors.WrongChannelError(
                f"This command only works in {team_bot_channel.mention} or {admin_bot_channel.mention}"
            )
        return True

    return commands.check(predicate)


def is_recruiter():
    def predicate(ctx):
        officer = ctx.bot.officer_manager.get_officer(ctx.author.id)
        if officer and officer.is_recruiter:
            return True
        else:
            raise errors.NotForYouError("This command is only for LPD Recruiters.")

    return commands.check(predicate)


def is_dev_team():
    def predicate(ctx):
        officer = ctx.bot.officer_manager.get_officer(ctx.author.id)
        if officer and officer.is_dev_member:
            return True
        else:
            raise errors.NotForYouError("This command is only for the LPD Dev Team.")

    return commands.check(predicate)


def is_chat_moderator():
    def predicate(ctx):
        officer = ctx.bot.officer_manager.get_officer(ctx.author.id)
        if officer and officer.is_chat_moderator:
            return True
        elif officer and officer.is_moderator:
            return True
        else:
            raise errors.NotForYouError("This command is only for LPD Chat Moderators.")

    return commands.check(predicate)


def is_moderator():
    def predicate(ctx):
        officer = ctx.bot.officer_manager.get_officer(ctx.author.id)
        if officer and officer.is_moderator:
            return True
        else:
            raise errors.NotForYouError("This command is only for LPD Moderators.")

    return commands.check(predicate)


def is_team_lead():
    def predicate(ctx):
        officer = ctx.bot.officer_manager.get_officer(ctx.author.id)
        if officer and officer.is_team_lead:
            return True
        else:
            raise errors.NotForYouError("This command is only for LPD Team Leads.")

    return commands.check(predicate)


def is_programming_team():
    def predicate(ctx):
        officer = ctx.bot.officer_manager.get_officer(ctx.author.id)
        if officer and officer.is_programming_team:
            return True
        else:
            raise errors.NotForYouError(
                "This command is only for the LPD Programming Team."
            )

    return commands.check(predicate)


def is_lmt_trainer():
    def predicate(ctx):
        officer = ctx.bot.officer_manager.get_officer(ctx.author.id)
        if officer and officer.is_lmt_trainer:
            return True
        else:
            raise errors.NotForYouError(
                "This command is only for the LMT Trainer Team."
            )

    return commands.check(predicate)
