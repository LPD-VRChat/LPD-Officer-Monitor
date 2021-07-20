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
from BusinessLayer.extra_functions import handle_error
from BusinessLayer.extra_functions import ts_print as print
import BusinessLayer.checks as checks


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.blue()

    @checks.is_chat_moderator()
    @commands.command()
    async def detain(self, ctx):
        """detain description"""
        pass

    @checks.is_moderator()
    @commands.command()
    async def restore(self, ctx):
        """restore description"""
        pass

    @checks.is_chat_moderator()
    @commands.command()
    async def strike(self, ctx):
        """strike description"""
        pass

    @checks.is_chat_moderator()
    @commands.command()
    async def list_strikes(self, ctx):
        """list_strikes description"""
        pass


def setup(bot):
    bot.add_cog(Moderation(bot))
