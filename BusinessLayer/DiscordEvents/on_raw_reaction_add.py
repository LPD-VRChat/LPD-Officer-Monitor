import asyncio
from discord.ext import commands


def _on_raw_reaction_add(bot: commands.Bot):
    async def on_raw_reaction_add(payload):
        if not bot.everything_ready:
            return

        # if someone reacts :x: in REQUEST_RANK_CHANNEL, and they are a trainer, delete the message
        if (
            payload.channel_id == Settings.REQUEST_RANK_CHANNEL
            and payload.emoji.name == "❌"
            and is_any_trainer(payload.user_id)
        ):
            message = await bot.get_message(payload.channel_id, payload.message_id)
            await bot.delete_message(message)

    return on_raw_reaction_add
