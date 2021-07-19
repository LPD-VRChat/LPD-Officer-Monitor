import asyncio
from discord.ext import commands


def _on_error(bot: commands.Bot):
    async def on_error(event, *args, **kwargs):
        if isinstance(args[0], HTTPException):
            return

        print(f"Error in {event}: {args}")
        traceback.print_exc()

    return on_error
