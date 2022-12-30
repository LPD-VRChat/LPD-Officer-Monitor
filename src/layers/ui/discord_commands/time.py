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
import src.layers.business

from src.layers.business.bl_wrapper import BusinessLayerWrapper
from src.layers.business.extra_functions import (
    send_long,
    now,
    interaction_send_long,
    parse_iso_date,
    interaction_reply,
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
        interac: discord.Interaction,
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
                    await interaction_reply(
                        interac, "invalid date `from_date` argument", ephemeral=True
                    )
                    return
                try:
                    to_dt = parse_iso_date(to_date)
                except (ValueError):
                    await interaction_reply(
                        interac, "invalid date `to_date` argument", ephemeral=True
                    )
                    return
            case (True, False):
                await interaction_reply(
                    interac, "you forgot `to_date` argument", ephemeral=True
                )
                return
            case (False, True):
                await interaction_reply(
                    interac, "you forgot `from_date` argument", ephemeral=True
                )
                return
        await interac.response.defer(ephemeral=False, thinking=True)

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
            interac,
            result,
        )

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(name="time_top", description="gives top patrolling times")
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    @app_cmd.describe(days="look up number of days in the past (default=28)")
    @app_cmd.describe(from_date="ISO 8601 format YYYY-MM-DD (days will be ignored)")
    @app_cmd.describe(to_date="ISO 8601 format YYYY-MM-DD (days will be ignored)")
    async def time_top_slash(
        self,
        interac: discord.Interaction,
        days: int = 28,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
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
                    await interaction_reply(
                        interac, "invalid date `from_date` argument", ephemeral=True
                    )
                    return
                try:
                    to_dt = parse_iso_date(to_date)
                except (ValueError):
                    await interaction_reply(
                        interac, "invalid date `to_date` argument", ephemeral=True
                    )
                    return
            case (True, False):
                await interaction_reply(
                    interac, "you forgot `to_date` argument", ephemeral=True
                )
                return
            case (False, True):
                await interaction_reply(
                    interac, "you forgot `from_date` argument", ephemeral=True
                )
                return

        await interac.response.defer(ephemeral=False, thinking=True)

        try:
            leaderboard = await self.bl_wrapper.pt_bl.get_top_patrol_time(
                from_dt=from_dt, to_dt=to_dt
            )
        except Exception as e:
            print(e)
            return

        leaderboard_lines = []
        for k, v in leaderboard.items():
            officer_name = await self.bl_wrapper.mm_bl.get_officer_vrcname_from_id(k)
            leaderboard_lines.append(f"{officer_name} = {v}")

        await interaction_send_long(
            interac,
            "\n".join(leaderboard_lines),
        )

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(
        name="list_promotable_recruits",
        description="List recruits that could be promoted to Officer",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    @app_cmd.describe(days="look up number of days in the past (default=28)")
    @app_cmd.describe(minimum="Minimum hours of patrol time")
    async def list_promotable_recruits(
        self,
        interac: discord.Interaction,
        minimum: int,
        days: int = 28,
    ):
        guild = self.bot.get_guild(settings.SERVER_ID)
        if not guild:
            raise Exception(f"guild {settings.SERVER_ID} is not accessible")

        role = guild.get_role(settings.ROLE_LADDER.recruit.id)
        if role is None:
            raise Exception(
                f"recruit role {settings.ROLE_LADDER.recruit.id} is not accessible"
            )
        from_dt = now() - dt.timedelta(days=days)
        result = await self.bl_wrapper.pt_bl.get_potential_officer_promotion(
            from_dt, minimum
        )
        mentions = " ".join(f"<@{officer.id}>" for officer in result)

        await interaction_reply(
            interac,
            f"Potential promotion to Officer {len(result)}/{len(role.members)}:\n"
            + mentions,
        )


async def setup(bot):
    await bot.add_cog(Time(bot))
