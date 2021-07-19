import asyncio
from discord.ext import commands


def _on_raw_bulk_message_delete(bot: commands.Bot):
    async def on_raw_bulk_message_delete(payload):
        # If the channel the LEAVE_OF_ABSENCE_CHANNEL, delete the LOA
        if payload.channel_id == Settings.LEAVE_OF_ABSENCE_CHANNEL:
            pass

    return on_raw_bulk_message_delete
