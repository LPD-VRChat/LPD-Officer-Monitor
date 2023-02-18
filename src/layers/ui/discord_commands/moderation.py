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
from discord import app_commands as app_cmd

# Custom
import src.layers.business.checks as checks
from src.layers.business.extra_functions import (
    msgbox_confirm,
    interaction_reply,
)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bl_wrapper: BusinessLayerWrapper = bot.bl_wrapper
        self.color = discord.Color.blue()

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(
        name="give_strike",
        description="List all renewawls of an officers",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    @app_cmd.describe(offender="The target of the strike")
    @app_cmd.describe(reason="The reason of the strike")
    async def give_strike(
        self,
        interac: discord.Interaction,
        offender: discord.Member,
        reason: str,
    ):
        if not await msgbox_confirm(
            interac,
            message=f"**Are you sure this strike is correct?**\nOffender: {offender.mention}  [{offender.id}]\nReason: {reason}",
        ):
            return
        await self.bl_wrapper.mod.give_strike(offender.id, reason, interac.user.id)
        await interaction_reply(interac, "Strike recorded")

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(
        name="list_strike",
        description="List all renewawls of an officers",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    @app_cmd.describe(offender="use this if user is still present in the guild")
    @app_cmd.describe(member_id="use this if user is gone form the guild")
    async def list_strike(
        self,
        interac: discord.Interaction,
        offender: discord.Member = None,
        member_id: str = None,
    ):
        """use `offender` if user is still present in the guild. use `member_id` if user is gone form the guild"""

        match (offender is None, member_id is None):
            case (True, True):
                await interaction_reply(interac, f"Define only one user, {__doc__}")
                return
            case (False, False):
                await interaction_reply(
                    interac, f"You need to define a user!!!, {__doc__}"
                )
                return
            case (False, True):
                user_id = offender.id
            case (True, False):
                try:
                    user_id = int(member_id)
                except (ValueError):
                    await interaction_reply(interac, f"Not a valid id, {__doc__}")
                    return

        strikes = await self.bl_wrapper.mod.list_strike(user_id)
        if len(strikes) == 0:
            await interaction_reply(
                interac, f"No stike against user <@{user_id}> [{user_id}]"
            )
            return
        message = "\n".join(
            [
                f"{s.timestamp.isoformat()} <@{s.submitter.id}> {s.reason}"
                for s in strikes
            ]
        )
        await interaction_reply(
            interac, f"Stikes against user <@{user_id}> [{user_id}] :\n{message}"
        )


async def setup(bot):
    await bot.add_cog(Moderation(bot))
