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
            raise errors.NotForYouError("This command is only for LPD Cheifs.")

    return commands.check(predicate)


def is_admin_bot_channel():
    def predicate(ctx):
        if ctx.message.channel.id != ctx.bot.settings["admin_bot_channel"]:
            raise errors.WrongChannelError(
                "This command only works in the admin bot channel."
            )
        return True

    return commands.check(predicate)


def is_general_bot_channel():
    def predicate(ctx):
        if (
            ctx.message.channel.id != ctx.bot.settings["admin_bot_channel"]
            and ctx.message.channel.id != ctx.bot.settings["general_bot_channel"]
        ):
            raise errors.WrongChannelError(
                "This command only works in the general bot channel or admin bot channel."
            )
        return True

    return commands.check(predicate)


def is_application_channel():
    def predicate(ctx):
        if (
            ctx.message.channel.id != ctx.bot.settings["admin_bot_channel"]
            and ctx.message.channel.id != ctx.bot.settings["application_channel"]
        ):
            raise errors.WrongChannelError(
                "This command only works in the application channel."
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
