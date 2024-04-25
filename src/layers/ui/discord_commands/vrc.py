# Settings import
from typing import Optional
import settings

# Standard
import logging
import datetime
import asyncio

# Community
import discord
from discord.ext import commands, tasks
from discord import app_commands as app_cmd
import ormar
from settings.classes import RoleLadderElement

# Custom
import src.layers.business.checks as checks
from src.layers.storage import models

from src.layers.business.bl_wrapper import BusinessLayerWrapper
from src.layers.business.extra_functions import (
    interaction_reply,
    interaction_send_str_as_file,
    has_role_id,
)

log = logging.getLogger("lpd-officer-monitor")


class VRC(commands.Cog):
    def __init__(self, bot):
        self.bl_wrapper: BusinessLayerWrapper = bot.bl_wrapper
        self.bot = bot
        self.color = discord.Color.lighter_grey()
        self.git_export_lock = asyncio.Lock()

    @checks.is_mugshot_diagnosis_channel(True)
    @checks.is_officer(True)
    @app_cmd.command(
        name="template",
        description="Produce a template for your Mugshot or Diagnosis",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    async def template_mugshot_diagnosis(self, interac: discord.Interaction):
        r = self.bl_wrapper.pt_bl.get_patrolling_officers()
        for channel_id in r:
            if interac.user.id in r[channel_id]:
                patrolling_officers = " ".join([f"<@{o}>" for o in r[channel_id]])
                break
        else:
            patrolling_officers = ""
        if interac.channel_id == settings.MUGSHOT_CHANNEL:
            message = (
                "Mugshot message Template\n"
                "```\n"
                "Name: \n"
                "Crimes: \n"
                f"Officers: {patrolling_officers}\n"
                "```\n"
                "Don't forget to add your pictures"
            )
        elif interac.channel_id == settings.DIAGNOSIS_CHANNEL:
            message = (
                "Diagnosis message Template\n"
                "```\n"
                "Patient: \n"
                "Diagnosis: \n"
                "Treatment: \n"
                f"LMTs: {patrolling_officers}\n"
                "```\n"
                "Don't forget to add your pictures"
            )
        else:
            message = "Command used in an unautorized channel"

        await interac.delete_original_response()
        await interaction_reply(
            interac,
            f"{message}",
            ephemeral=True,
        )

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
            f"Your VRChat username has been unlinked\nPlease use `/vrc_link` command to set your new VRChat username.",
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
        output_text = await self.bl_wrapper.member_list.get_csv_str()

        await interaction_send_str_as_file(
            interac, output_text, "allowlist.csv", "Allowlist:"
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

    @checks.is_team_bot_channel(True)
    @checks.app_cmd_check_any(
        checks.is_dev_team(True),
        checks.is_white_shirt(True),
        checks.is_programming_team(True),
    )
    @app_cmd.command(
        name="vrc_list_json",
        description="List linked VRChat account for world allowlist in JSON",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    async def list_dev_json(self, interac: discord.Interaction):
        output_text = await self.bl_wrapper.vrc.get_list_as_json()
        await interaction_send_str_as_file(
            interac, output_text, "allowlist.json", "Allowlist:"
        )

    @commands.hybrid_command(
        name="vrc_list_export",
        description="Re-export list linked VRChat account for world allowlist in JSON",
    )
    @checks.is_team_bot_channel()
    # @checks.app_cmd_check_any(
    @commands.check_any(
        checks.is_dev_team(),
        checks.is_white_shirt(),
        checks.is_programming_team(),
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    async def list_export_json(self, ctx):
        async with self.git_export_lock:
            if await self.bl_wrapper.vrc.export_json_list_git():
                await ctx.send("Done")
            else:
                await ctx.send(":red_circle: An error occured!")

    @tasks.loop(
        time=[
            datetime.time(00, 00, tzinfo=datetime.UTC),
            # datetime.time(12, 00, tzinfo=datetime.UTC),
        ]
    )
    async def git_auto_export(self):
        # didn't seem to work in dev
        # task are only possible in cog, dosn't work in bl
        if settings.GIT_AUTO_EXPORT:
            async with self.git_export_lock:
                await self.bl_wrapper.vrc.export_json_list_git()

    @git_auto_export.error
    async def git_auto_export_except(self, ex):
        log.exception("An error occurred: %s", str(ex))

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.git_auto_export.is_running():
            self.git_auto_export.start()

    def cog_unload(self):
        self.git_auto_export.cancel()


async def setup(bot):
    await bot.add_cog(VRC(bot))
