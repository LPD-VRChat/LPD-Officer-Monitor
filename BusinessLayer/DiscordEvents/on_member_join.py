import asyncio
from discord.ext import commands


def _on_member_join(bot: commands.Bot):
    async def on_member_join(member):
        if member.bot:
            return

        # If the member is a detainee, make sure to give them the detention role
        pass

    return on_member_join
