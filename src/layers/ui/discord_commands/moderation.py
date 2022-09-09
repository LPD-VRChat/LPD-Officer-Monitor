# Settings import
from src.layers.business.bl_wrapper import BusinessLayerWrapper
import settings

# Standard
import traceback
import asyncio
import argparse

# Community
import discord
from discord.ext import commands

# Custom
import src.layers.business.checks as checks


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bl_wrapper: BusinessLayerWrapper = bot.bl_wrapper
        self.color = discord.Color.blue()


async def setup(bot):
    await bot.add_cog(Moderation(bot))
