# Settings import
from typing import Optional
import settings

# Standard
import logging

# Community
import discord
from discord.ext import commands
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
        officers = (
            await models.Officer.objects.filter(models.Officer.deleted_at.isnull(True))
            .exclude(models.Officer.vrchat_name == "")
            .all()
        )

        # because we get all ranks and inverted the order to replicate
        # the old behavior we need to do a local version of the function
        all_ranks = list(reversed(settings.ROLE_LADDER.__dict__.values()))

        def get_lpd_member_rank_local(
            member: discord.Member,
        ) -> Optional[RoleLadderElement]:
            for rank in all_ranks:
                if has_role_id(member, rank.id):
                    return rank
            return None

        output_text = ""
        output_text += settings.NAME_SEPARATOR.join(
            [
                "Name",
                "Rank",
                "Staff",
                "SLRT Certified",
                "LMT Certified",
                "CO Certified",
                "Event Host",
                "Programmer",
                "Media",
                "Chatmod",
                "Instigator",
                "Trainer",
                "SLRT Trainer",
                "LMT Trainer",
                "CO Trainer",
                "Instigator Trainer",
                "Dev",
                "Recruiter",
                "Lead",
                "Korean",
                "Chinese",
                "Community",
                "Backroom Access",
            ]
        )
        output_text += "\n"

        for o in officers:
            member = o.member(self.bot)
            if not member:
                log.error(f"officer {o.id} isn't on discord")
                continue
            rank = get_lpd_member_rank_local(member)
            if not rank:
                log.error(f"officer {o.id} does not have a rank")
                continue

            odata = [
                o.vrchat_name,
                rank.name,
                rank.is_white_shirt,
                has_role_id(member, settings.SLRT_TRAINED_ROLE),
                has_role_id(member, settings.LMT_TRAINED_ROLE),
                has_role_id(member, settings.WATCH_OFFICER_ROLE),
                has_role_id(member, settings.EVENT_HOST_ROLE),
                has_role_id(member, settings.PROGRAMMING_TEAM_ROLE),
                has_role_id(member, settings.MEDIA_PRODUCTION_ROLE),
                has_role_id(member, settings.CHAT_MODERATOR_ROLE),
                has_role_id(member, settings.INSTIGATOR_ROLE),
                has_role_id(member, settings.TRAINER_ROLE),
                has_role_id(member, settings.SLRT_TRAINER_ROLE),
                has_role_id(member, settings.LMT_TRAINER_ROLE),
                has_role_id(member, settings.PRISON_TRAINER_ROLE),
                has_role_id(member, settings.INSTIGATOR_TRAINER_ROLE),
                has_role_id(member, settings.DEV_TEAM_ROLE),
                has_role_id(member, settings.RECRUITER_ROLE),
                has_role_id(member, settings.TEAM_LEAD_ROLE),
                has_role_id(member, settings.KOREAN_ROLE),
                has_role_id(member, settings.CHINESE_ROLE),
                "LPD" if has_role_id(member, settings.LPD_ROLE) else "UKN",
                True,  # "Backroom Access",
            ]
            output_text += settings.NAME_SEPARATOR.join(map(str, odata)) + "\n"

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


async def setup(bot):
    await bot.add_cog(VRC(bot))
