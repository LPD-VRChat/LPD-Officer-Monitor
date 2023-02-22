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

    @checks.is_team_bot_channel(True)
    @checks.is_chat_moderator(True)
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
        strikes = await self.bl_wrapper.mod.give_strike(
            offender.id,
            reason,
            interac.user.id,
        )
        await interaction_reply(
            interac,
            f"Strike recorded.\nNumber of strikes in last 2 week: {strikes[0]}\nToal number of strikes: {strikes[1]}",
        )
        if strikes[0]:
            await interaction_reply(
                interac,
                f"<@&{settings.MODERATOR_ROLE}> <@{offender.id}> have received at least 3 strikes in the last two weeks.",
            )

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

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(
        name="detain_user",
        description="Detain a user",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    @app_cmd.describe(offender="use this if user is still present in the guild")
    @app_cmd.describe(member_id="use this if user is gone form the guild")
    async def detain_user(
        self,
        interac: discord.Interaction,
        reason: str,
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

        if not await msgbox_confirm(
            interac,
            message=f"**Are you sure you want this user to be detained?**\nOffender: <@{user_id}  [{user_id}]\nReason: {reason}",
        ):
            return
        await self.bl_wrapper.mod.detain_user(user_id, reason)
        await interaction_reply(interac, f"User have been detained")

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(
        name="release_detained_user",
        description="Release detained user",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    @app_cmd.describe(offender="use this if user is still present in the guild")
    @app_cmd.describe(member_id="use this if user is gone form the guild")
    async def release_detained_user(
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

        if not await msgbox_confirm(
            interac,
            message=f"**Are you sure you want this user to be Released?**\nOffender: <@{user_id}  [{user_id}]",
        ):
            return

        result = await self.bl_wrapper.mod.release_detained_user(user_id)

        if result:
            await interaction_reply(interac, f"User have been released")
        else:
            await interaction_reply(
                interac,
                f"One of the released operation may have failed.\nPlease check the bot logs",
            )


async def setup(bot):
    await bot.add_cog(Moderation(bot))
