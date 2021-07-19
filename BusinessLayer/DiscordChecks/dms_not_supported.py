import asyncio
from discord.ext import commands


def _dms_not_supported(bot: commands.Bot):
    def dms_not_supported(ctx):
        if ctx.guild is None:
            print(f"{ctx.author} tried to DM me in {ctx.channel}")
            raise commands.NoPrivateMessage(
                "This bot does not support direct messages. Please use a server channel instead."
            )
        else:
            return True

    return dms_not_supported
