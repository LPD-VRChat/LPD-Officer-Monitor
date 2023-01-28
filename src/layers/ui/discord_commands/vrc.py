# Settings import
import settings

# Standard
import logging

# Community
import discord
from discord.ext import commands
from discord import app_commands as app_cmd
import ormar

# Custom
import src.layers.business.checks as checks
from src.layers.storage import models

from src.layers.business.bl_wrapper import BusinessLayerWrapper
from src.layers.business.extra_functions import (
    interaction_reply,
    interaction_send_str_as_file,
)

log = logging.getLogger("lpd-officer-monitor")


class VRC(commands.Cog):
    def __init__(self, bot):
        self.bl_wrapper: BusinessLayerWrapper = bot.bl_wrapper
        self.bot = bot
        self.color = discord.Color.lighter_grey()

    @checks.is_general_bot_channel(True)
    @checks.is_officer(True)
    @app_cmd.command(
        name="vrc_info",
        description="Display the current linked VRChat account",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    async def info(self, interac: discord.Interaction):
        try:
            officer = await models.Officer.objects.get(id=interac.user.id)
        except ormar.NoMatch:
            log.error(f"officer {interac.user.id} is not registered")
            await interaction_reply(
                interac, "You are unregistered officer, contact staff"
            )
            return

        if len(officer.vrchat_name):
            await interaction_reply(
                interac, f"Your VRChat name is `{officer.vrchat_name}`"
            )
        else:
            await interaction_reply(
                interac,
                f"Your VRChat name is not set.\n Please use `/vrc_link` command to set your username.",
            )

    @checks.is_general_bot_channel(True)
    @checks.is_officer(True)
    @app_cmd.command(
        name="vrc_link",
        description="Link your VRChat username to your discord account",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    @app_cmd.describe(name="Vrchat name")
    async def link(self, interac: discord.Interaction, name: str):
        try:
            officer = await models.Officer.objects.get(id=interac.user.id)
        except ormar.NoMatch:
            log.error(f"officer {interac.user.id} is not registered")
            await interaction_reply(interac, "You are unregistered, contact staff")
            return

        if settings.NAME_SEPARATOR in name:
            await interaction_reply(
                interac,
                f"A forbidden character is used in the username.\nPlease remove `{settings.NAME_SEPARATOR}` from your username",
            )
            return

        officer.vrchat_name = name
        await officer.update()
        await interaction_reply(
            interac, f"Your VRChat name is set to `{officer.vrchat_name}`"
        )

    @checks.is_general_bot_channel(True)
    @checks.is_officer(True)
    @app_cmd.command(
        name="vrc_unlink",
        description="Unlinked VRChat username",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    async def unlink(self, interac: discord.Interaction):
        try:
            officer = await models.Officer.objects.get(id=interac.user.id)
        except ormar.NoMatch:
            log.error(f"officer {interac.user.id} is not registered")
            await interaction_reply(interac, "You are unregistered, contact staff")
            return

        officer.vrchat_name = ""
        await officer.update()

        await interaction_reply(
            interac,
            f"Your VRChat username as been unlinked\nPlease use `/vrc_link` command to set your username.",
        )

    @checks.is_team_bot_channel(True)
    @checks.app_cmd_check_any(checks.is_dev_team(True), checks.is_white_shirt(True))
    @app_cmd.command(
        name="vrc_list_dev",
        description="List linked VRChat account for world allowlist",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    async def list_dev(self, interac: discord.Interaction):
        officers = (
            await models.Officer.objects.filter(models.Officer.deleted_at.isnull(True))
            .exclude(models.Officer.vrchat_name == "")
            .all()
        )

        output_text = (
            f"{settings.NAME_SEPARATOR.join( [o.vrchat_name for o in officers] )}"
        )

        await interaction_send_str_as_file(
            interac, output_text, "allowlist.txt", "Allowlist:"
        )

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(
        name="vrc_list_readable",
        description="List linked VRChat account for hoomans",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    async def list_hooman_readable(self, interac: discord.Interaction):
        guild = self.bot.get_guild(settings.SERVER_ID)
        officers = (
            await models.Officer.objects.filter(models.Officer.deleted_at.isnull(True))
            .exclude(models.Officer.vrchat_name == "")
            .all()
        )
        out_string = "**All linked accounts:**\n**Discord - VRChat**\n"

        for o in officers:
            member = guild.get_member(o.id)
            add = f"`{member.display_name}` - `{o.vrchat_name}`\n"
            if len(add) + len(out_string) >= 2000:
                await interaction_reply(interac, out_string)
                out_string = add
            else:
                out_string += add

        await interaction_reply(interac, out_string)


async def setup(bot):
    await bot.add_cog(VRC(bot))
