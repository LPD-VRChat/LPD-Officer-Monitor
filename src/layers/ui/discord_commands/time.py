# Settings import
import settings

# Standard
import datetime as dt
from typing import Optional

# Community
import discord
from discord.ext import commands
from discord import app_commands as app_cmd

# Custom
import src.layers.business.checks as checks
import src.layers.business.errors as errors

from src.layers.business.bl_wrapper import BusinessLayerWrapper
from src.layers.business.extra_functions import (
    send_long,
    now,
    interaction_send_long,
    parse_iso_date,
)


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

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(name="time_patrols", description="Returns patrol times")
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    @app_cmd.describe(officer="list the members of this role")
    @app_cmd.describe(days="look up number of days in the past (default=28)")
    @app_cmd.describe(from_date="ISO 8601 format YYYY-MM-DD (days will be ignored)")
    @app_cmd.describe(to_date="ISO 8601 format YYYY-MM-DD (days will be ignored)")
    @app_cmd.describe(full_list="list all the patrols, else list total patrol time")
    async def time_slash(
        self,
        iterac: discord.Interaction,
        officer: discord.Member,
        days: int = 28,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        full_list: bool = False,
    ):

        from_dt = now() - dt.timedelta(days=days)
        to_dt = now()
        match (from_date is None, to_date is None):
            case (True, True):
                pass
            case (False, False):
                try:
                    from_dt = parse_iso_date(from_date)
                except (ValueError):
                    await iterac.response.send_message(
                        "invalid date `from_date` argument", ephemeral=True
                    )
                    return
                try:
                    to_dt = parse_iso_date(to_date)
                except (ValueError):
                    await iterac.response.send_message(
                        "invalid date `to_date` argument", ephemeral=True
                    )
                    return
            case (True, False):
                await iterac.response.send_message(
                    "you forgot `to_date` argument", ephemeral=True
                )
                return
            case (False, True):
                await iterac.response.send_message(
                    "you forgot `from_date` argument", ephemeral=True
                )
                return
        # defer as some issue where responce will be stuck as thinking because it's sent after definitive responce
        # await iterac.response.defer(ephemeral=False, thinking=True)

        if full_list:
            patrols = await self.bl_wrapper.pt_bl.get_patrols(
                officer.id, from_dt=from_dt, to_dt=to_dt
            )
            results = []
            for p in patrols:
                await p.main_channel.load()  # propably very bad
                results.append(
                    f"{p.start.isoformat(sep=' ', timespec='seconds')}  {str(p.duration())} {'in event' if p.event else 'freeroam'} {p.main_channel.name}"
                )
            result = "\n".join(results)

        else:
            result = str(
                await self.bl_wrapper.pt_bl.get_patrol_time(
                    officer.id, from_dt=from_dt, to_dt=to_dt
                )
            )

        await interaction_send_long(
            iterac,
            result,
        )


async def setup(bot):
    await bot.add_cog(Time(bot))
