import asyncio
from discord.ext import commands
from BusinessLayer.test_functions import is_officer


def _on_member_update(bot: commands.Bot):
    async def on_member_update(before, after):
        if before.bot or after.bot:
            return

        officer_before = is_officer(before.id)
        officer_after = is_officer(after.id)

        if officer_before and officer_after:
            return

        elif not officer_before and not officer_after:
            return

        elif not officer_before and officer_after:
            create_officer(after.id)

        elif officer_before and not officer_after:
            remove_officer(after.id)

    return on_member_update
