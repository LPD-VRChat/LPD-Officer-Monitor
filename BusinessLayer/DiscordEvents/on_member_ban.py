import asyncio
from discord.ext import commands


def _on_member_ban(bot: commands.Bot):
    async def on_member_ban(member):
        if is_officer(member.id):
            remove_officer(member.id)

    return on_member_ban
