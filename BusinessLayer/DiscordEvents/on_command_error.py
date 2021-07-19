import asyncio
import traceback
from discord.ext import commands


def _on_command_error(bot: commands.Bot):
    async def on_command_error(ctx, exception):
        exception_string = str(exception).replace(
            "raised an exception", "encountered a problem"
        )

        try:
            await ctx.send(exception_string)
        except discord.Forbidden:
            bot.get_channel(Settings.ERROR_LOG_CHANNEL).send(
                f"**{ctx.author}**, I'm not allowed to send messages in {ctx.channel}**"
            )
            pass

        if exception_string.find("encountered a problem") != -1:
            print(
                exception_string,
                "".join(traceback.format_exception(None, exception, None)),
            )

    return on_command_error
