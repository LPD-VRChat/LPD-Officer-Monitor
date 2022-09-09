# Settings import
import settings

# Standard
import datetime as dt

# Community
import discord
from discord.ext import commands

# Custom
import src.layers.business.checks as checks
import src.layers.business.errors as errors

from src.layers.business.bl_wrapper import BusinessLayerWrapper
from src.layers.business.extra_functions import send_long, now


class Time(commands.Cog):
    def __init__(self, bot):
        self.bl_wrapper: BusinessLayerWrapper = bot.bl_wrapper
        self.bot = bot
        self.color = discord.Color.blue()

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command()
    async def time(self, ctx: commands.Context, officer: discord.Member):
        """
        TEMPORARY TEST COMMAND
        """
        await send_long(
            ctx.channel,
            str(
                await self.bl_wrapper.pt_bl.get_patrol_time(
                    officer.id, from_dt=now() - dt.timedelta(days=28), to_dt=now()
                )
            ),
        )

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command()
    async def time_patrols(self, ctx: commands.Context, officer: discord.Member):
        """
        TEMPORARY TEST COMMAND
        """
        await send_long(
            ctx.channel,
            str(
                await self.bl_wrapper.pt_bl.get_patrols(
                    officer.id, from_dt=now() - dt.timedelta(days=28), to_dt=now()
                )
            ),
        )

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command()
    async def time_patrol_voices(self, ctx: commands.Context, officer: discord.Member):
        """
        TEMPORARY TEST COMMAND
        """
        await send_long(
            ctx.channel,
            str(
                await self.bl_wrapper.pt_bl.get_patrol_voices(
                    officer.id, from_dt=now() - dt.timedelta(days=28), to_dt=now()
                )
            ),
        )


async def setup(bot):
    await bot.add_cog(Time(bot))
