import asyncio
from discord.ext import commands


def _on_voice_state_update(bot: commands.Bot):
    async def on_voice_state_update(member, before, after):
        if member.id == bot.user.id:
            return

        if after.channel == before.channel:
            return

        if (
            after.channel.category_id not in Settings.ON_DUTY_CATEGORY
            or before.channel.category_id not in Settings.ON_DUTY_CATEGORY
        ):
            return

        # If member is not an officer, return
        if not is_officer(member.id):
            return

        if after.channel is None:
            # User left the voice channel
            pass

        elif after.channel.id == Settings.VOICE_CHANNEL_ID:
            # User joined the voice channel
            pass

        elif after.channel.id != before.channel.id:
            # User changed voice channels
            pass

        if after.channel is not None:
            # Archive the voice activity
            pass

    return on_voice_state_update
