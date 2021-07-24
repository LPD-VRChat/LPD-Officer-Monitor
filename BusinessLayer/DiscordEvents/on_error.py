import asyncio
import traceback
from discord.ext import commands
from discord.errors import HTTPException


def _on_error(bot: commands.Bot):
    async def on_error(event, *args, **kwargs):
        if isinstance(args[0], HTTPException):
            return

        print(f"Error in {event}: {args}")
        traceback.print_exc()

    return on_error
