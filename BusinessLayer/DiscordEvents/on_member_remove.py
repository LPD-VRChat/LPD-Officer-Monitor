import asyncio
from discord.ext import commands


def _on_member_remove(bot: commands.Bot):
    async def on_member_remove(member):
        if is_officer(member.id):
            remove_officer(member.id)

    return on_member_remove
