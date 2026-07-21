# Settings import
import settings

# Standard
import datetime as dt
import logging
import asyncio
from typing import Optional

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
    mention_slash_cmd,
    msgbox_confirm,
    multi_choice_embed,
)
from src.layers.business.vrc_name_bl import (
    LinkSearchResult,
    VrcNotWorking,
    LinkInviteResult,
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
            txt = f"""Your VRChat name is `{officer.vrchat_name}`
Your id is `{officer.vrchat_id}`"""
            if settings.CONFIG_LOADED == "dev":
                if officer.extra:
                    txt += f"DEVONLY: {officer.extra.get('vrcRegStatus')}"
                else:
                    txt += f"DEVONLY: no extra"
            await interaction_reply(interac, txt)
        else:
            await interaction_reply(
                interac,
                f"Your VRChat name is not set.\n Please use {await mention_slash_cmd(self.bot,'vrc_link')} command to set your username.",
            )

    @checks.is_general_bot_channel(True)
    @checks.is_officer(True)
    @app_cmd.command(
        name="vrc_link",
        description="Link your VRChat username to your discord account",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    @app_cmd.describe(name="Vrchat name, URL or UUID")
    async def link(self, interac: discord.Interaction, name: str):
        result_search, users = LinkSearchResult.ERROR, []
        try:
            result_search, users = await self.bl_wrapper.vrc.link_search(
                interac.user.id, name
            )
        except BaseException as e:
            log.exception("lookup failed badly")
        except VrcNotWorking:
            await interaction_reply(
                interac,
                ":warning:You are registered, but VRChat api is disabled, we will invite you soon",
            )
            return
        match (result_search):
            case LinkSearchResult.OK:
                self.bl_wrapper.member_list.upload_to_world(reason="link")
            case LinkSearchResult.VRCAPI_DOWN:
                self.bl_wrapper.member_list.upload_to_world(reason="link")
                txt = f":white_check_mark: Your VRChat name is set to `{name}`\n"
                if settings.VRC_ENABLED:
                    txt = ":warning: but VRChat api is disabled"
                    if len(settings.VRC_GROUP_ID):
                        txt += f", you can [join here](<https://vrchat.com/home/group/{settings.VRC_GROUP_ID}>)"
                    else:
                        txt += " we will invite you soon"
                await interaction_reply(interac, txt)
                return
            case LinkSearchResult.INVALID_UUID:
                await interaction_reply(
                    interac,
                    ":warning:The UUID/URL is invalid. Double check it and try again",
                )
                return
            case LinkSearchResult.ERROR:
                await interaction_reply(
                    interac, ":red_circle:An error happened, contact staff"
                )
                return
            case LinkSearchResult.USER_SEARCH_DISABLED:
                await interaction_reply(
                    interac,
                    """:warning:User search is disabled.
Go to ![VRChat website](<https://vrchat.com/home>) and copy the link when hovering your name.
Or in VRCX, copy `User ID`""",
                )
                return
            case _:
                log.error(f"link_search error not handled {result_search}")
                await interaction_reply(
                    interac, ":red_circle:An error happened, contact staff"
                )
                return

        if users is None or len(users) == 0:
            await interaction_reply(
                interac, ":red_circle:Could not find any user, use id or URL"
            )
            return

        def vrc_user_2_embed(user_info) -> discord.Embed:
            embed = discord.Embed(
                title=f"{user_info.display_name}",
                description="",
                # color=color,
            )
            embed.add_field(name="Display Name", value=f"{user_info.display_name}")
            embed.add_field(name="ID", value=f"{user_info.id}")
            embed.add_field(name="Last Platform", value=f"{user_info.last_platform}")
            if user_info.pronouns:
                embed.add_field(name="Pronouns", value=f"{user_info.pronouns}")
            if user_info.bio_links and len(user_info.bio_links):
                embed.add_field(name="Links", value=f"{str(user_info.bio_links)[:500]}")
            if hasattr(user_info, "age_verified"):
                embed.add_field(
                    name="Age verified", value=f"{user_info.age_verification_status}"
                )
            if hasattr(user_info, "badges") and len(user_info.badges):
                embed.add_field(name="badges", value=f"{len(user_info.badges)}")
            if hasattr(user_info, "state"):
                embed.add_field(name="State", value=f"{user_info.state}")
                embed.add_field(name="Status", value=f"{user_info.status}")
            if settings.VRC_FEAT_DISPLAY_USER_IMAGE:
                embed.set_thumbnail(
                    url=(
                        user_info.user_icon
                        if len(user_info.user_icon)
                        else user_info.current_avatar_thumbnail_image_url
                    )
                )  # doesn't work in discord because of the redirect
            return embed

        selected_user = -1
        if len(users) == 1:
            embed = vrc_user_2_embed(users[0])
            embed.title = "Confirm this is your Vrchat Account"
            embed.description = ""

            if not await msgbox_confirm(interac, embed=embed, ephemeral=True):
                return
            selected_user = 0
        else:
            # print(users)
            embeds = [vrc_user_2_embed(u) for u in users]
            r = await multi_choice_embed(
                interac,
                embeds,
                "Looks like you missed typed your username and we could not find you.\nPlease Choose one of the users if they correspond to you:",
                ephemeral=True,
                button_labels=[u.display_name for u in users],
                cancel_button=True,
            )
            if r == -1:
                return
            selected_user = r

        await self.bl_wrapper.vrc.link_vrc(
            interac.user.id,
            users[selected_user].id,
            users[selected_user].display_name,
        )
        result_invite = await self.bl_wrapper.vrc.link_group_invite(
            interac.user.id,
            users[selected_user].id,
            users[selected_user].display_name,
        )
        match (result_invite):
            case LinkInviteResult.ok:
                await interaction_reply(
                    interac,
                    ":white_check_mark: You are registered, you should have received an invite for the VRChat group",
                )
            case LinkInviteResult.ALREADY_INVITED:
                await interaction_reply(
                    interac,
                    ":white_check_mark: You are registered, you **already** have an invite for the VRChat group",
                )
            case LinkInviteResult.ERROR:

                await interaction_reply(
                    interac,
                    ":warning: You are registered, but invite for the VRChat group failed",
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
        await self.bl_wrapper.vrc.unlink(interac.user.id)
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
        name="vrc_make_payments",
        description="Pay all the officers for the last week manually",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    async def make_payments(self, interac: discord.Interaction):
        last_paid: Optional[dt.datetime] = await models.Payment.objects.max("timestamp")
        last_paid = last_paid.replace(tzinfo=dt.UTC)
        now = dt.datetime.now(tz=dt.UTC)
        start_prev_week = now.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - dt.timedelta(days=now.weekday() + 7)
        end_prev_week = (start_prev_week + dt.timedelta(days=6)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        last_paid_str = ""
        if last_paid is None:
            last_paid_str = "They have never been paid."
        elif last_paid > end_prev_week and last_paid < now:
            last_paid_str = (
                f"# :warning: Officers already got paid for previous week!!! :warning:\n"
                + f"They were last paid on <t:{int(last_paid.timestamp())}:F> for the week of <t:{int(start_prev_week.timestamp())}:F> to <t:{int(end_prev_week.timestamp())}:F>\n"
                + "This means they will receive a new salary!!!"
            )
        else:
            start_last_week = last_paid.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - dt.timedelta(days=last_paid.weekday() + 7)
            end_last_week = (start_last_week + dt.timedelta(days=6)).replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            last_paid_str = (
                f"They were last paid on <t:{int(last_paid.timestamp())}:F> for the week of <t:{int(start_last_week.timestamp())}:F> to <t:{int(end_last_week.timestamp())}:F>\n"
                + f"The patrol time window will be from <t:{int(start_prev_week.timestamp())}:F> to <t:{int(end_prev_week.timestamp())}:F>\n"
            )

        if not await msgbox_confirm(
            interac,
            message="Are you sure you want to pay the officers for the past week manually?"
            + "\n"
            + last_paid_str,
        ):
            return

        await self.bl_wrapper.member_list.make_payments()
        await interaction_reply(interac, "Everyone has been paid successfully.")

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
        output_text = await self.bl_wrapper.member_list.get_json_str()
        await interaction_send_str_as_file(
            interac, output_text, "allowlist.json", "Allowlist:"
        )


async def setup(bot):
    await bot.add_cog(VRC(bot))
