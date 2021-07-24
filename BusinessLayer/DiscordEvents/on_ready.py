import asyncio
from discord.ext import commands
import Settings


def _on_ready(bot: commands.Bot):
    async def on_ready():
        print(f"Logged in as: {bot.user.name}")
        bot.guild = bot.get_guild(Settings.SERVER_ID)
        if bot.guild:
            print(f"Server Name : {bot.guild.name}\nServer ID   : {bot.guild.id}")
        if bot.has_been_started:
            await bot.shutdown(
                bot, location="disconnection", person="automatic recovery", exit=False
            )

        # This should be the last line in this function
        bot.has_been_started = True

    return on_ready
