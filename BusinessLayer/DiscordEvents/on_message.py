import asyncio
from discord.ext import commands


def _on_message(bot: commands.Bot):
    async def on_message(message):
        if message.author.bot:
            return

        elif message.channel.id in Settings.ALLOWED_COMMAND_CHANNELS:
            await bot.process_commands(message)

        elif message.channel.id == Settings.LEAVE_OF_ABSENCE_CHANNEL:
            # Process the LOA request
            pass

        elif message.channel.id == Settings.REQUEST_RANK_CHANNEL:
            # Process the rank request
            pass

        if message.channel.id not in Settings.IGNORED_CATEGORIES:
            # Archive the message activity
            pass

    return on_message
