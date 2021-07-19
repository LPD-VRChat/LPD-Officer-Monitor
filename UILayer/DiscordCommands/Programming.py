# Settings import
import Settings

# Standard
import traceback
import asyncio
import argparse

# Community
import discord
from discord.ext import commands

# Mine
from BusinessLayer.extra_functions import handle_error, clean_shutdown
from BusinessLayer.extra_functions import ts_print as print
import BusinessLayer.checks as checks


class Programming(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.red()

    @checks.is_team_bot_channel()
    @checks.is_programming_team()
    @commands.command()
    async def shutdown(self, ctx):
        """This command shuts the bot down cleanly"""
        await ctx.send("Shutting the bot down...")
        await clean_shutdown(
            self.bot, ctx.channel.name, ctx.author.display_name, exit=True
        )

    @checks.is_team_bot_channel()
    @checks.is_programming_team()
    @commands.command()
    async def restart(self, ctx):
        """Restarts the bot if something is broken"""
        await ctx.send("Restarting the bot...")
        await clean_shutdown(
            self.bot, ctx.channel.name, ctx.author.display_name, exit=False
        )

    @checks.is_team_bot_channel()
    @checks.is_programming_team()
    @commands.command()
    async def web(self, ctx):
        """web description"""
        pass

    @checks.is_team_bot_channel()
    @checks.is_programming_team()
    @commands.command()
    async def reload_module(self, ctx, module_name: str):
        """Reloads a module"""
        module = f"UILayer.DiscordCommands.{module_name}"
        try:
            self.bot.reload_extension(module)
            await ctx.send(f"Successfully reloaded {module_name}")
        except Exception as e:
            await ctx.send(f"Failed to reload {module_name}")
            await handle_error(self.bot, e, traceback.format_exc)


def setup(bot):
    bot.add_cog(Programming(bot))
