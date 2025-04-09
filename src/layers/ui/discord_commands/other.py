# Settings import
import settings

# Standard
import argparse
from typing import List, Literal, Optional, Set, Tuple
import logging
import datetime as dt
from zoneinfo import ZoneInfo

# Community
import discord
from discord.ext import commands
from thefuzz.process import extractBests
from discord import app_commands

# Custom
import src.layers.business.checks as checks
import src.layers.business.errors as errors

from src.layers.business.bl_wrapper import BusinessLayerWrapper
from src.layers.business.extra_functions import (
    get_calendar_events,
    get_monday_from_week,
    interaction_reply,
    interaction_send_long,
    send_long,
)

log = logging.getLogger("lpd-officer-monitor")


class Other(commands.Cog):
    def __init__(self, bot):
        self.bl_wrapper: BusinessLayerWrapper = bot.bl_wrapper
        self.bot = bot
        self.color = discord.Color.green()

    @staticmethod
    def remove_name_decoration(name: str) -> str:
        """
        Remove the discord special characters at the start and end of the string
        """
        return name.strip("| ⠀ ")

    def get_role_by_name(self, role_name: str) -> discord.Role:
        """
        Returns a role object from a given name
        """
        role_names = []

        for role in self.bot.guild.roles:
            sanitized_name = self.remove_name_decoration(role.name)
            role_names.append(sanitized_name)
            if sanitized_name.lower() == role_name.lower():
                return role
        msg = f"The role `{role_name}` could not be found.\n Did you mean: `{', '.join(role_names)}`?"
        cutoff_score = 75
        suggestions: List[Tuple[str, int]] = []

        # usually you get something on the first run, sometimes if you write really badly you won't get anything
        # lower the score to get more suggestions
        while len(suggestions) < 1 and len(role_name) > 1 and cutoff_score > 0:
            suggestions = extractBests(role_name, role_names, score_cutoff=cutoff_score)
            # if only one suggestion, give result immediately instead of suggest and having to type cmd again
            if cutoff_score == 75 and len(suggestions) == 1:
                try:
                    return self.get_role_by_name(suggestions[0][0])
                except errors.GetRoleMembersError as e:
                    print(
                        f"ERROR: rtv, Could not find role `{suggestions[0][0]}`, msg:",
                        e,
                    )
                    pass  # if role not found, we use original name to find suggestions

            cutoff_score -= 25

        for suggest in suggestions:
            # it's better to include quotes for copy paste correct role
            if " " in suggest[0]:
                msg += f'  `"{suggest[0]}"`'
            else:
                msg += f"  `{suggest[0]}`"
        raise errors.GetRoleMembersError(message=msg)

    def get_role_members(self, role: discord.Role) -> List[discord.Member]:
        # Make sure that people have the role
        if not role.members:
            raise errors.GetRoleMembersError(message=f"`{role.name}` is empty.")

        # Sort the members
        return sorted(
            role.members, key=lambda m: self.remove_name_decoration(m.name).lower()
        )

    @checks.is_team_bot_channel()
    @commands.check_any(
        checks.is_dev_team(), checks.is_team_lead(), checks.is_white_shirt()
    )
    @commands.command(usage="discordRole | -i includedRole -x excludedRole")
    async def rtv(self, ctx, *arguments):
        """This command searches server members, and returns a list of members having the role"""
        if arguments and "-i" not in arguments and "--include" not in arguments:
            if arguments[0] == "-x" or arguments[0] == "--exclude":
                role_names = [123]

            if arguments and "-x" not in arguments and "--exclude" not in arguments:
                excluded_role_names = None

        if ctx.message.clean_content.strip() == f"{settings.BOT_PREFIX}rtv":
            raise errors.MissingArgumentError(message="Missing arguments.")

        if (
            "-i" not in arguments
            and "--include" not in arguments
            and "-x" not in arguments
            and "--exclude" not in arguments
        ):
            role_names = [" ".join(arguments)]
            excluded_role_names = None

        else:
            parser = argparse.ArgumentParser()
            parser.add_argument("-i", "--include", action="append")
            parser.add_argument("-x", "--exclude", action="append")

            try:
                parsed = parser.parse_args(arguments)
            except:
                await ctx.send(
                    "When searching for multiple roles, you must provide all roles as arguments."
                )
                return

            if parsed.include:
                role_names = parsed.include
            else:
                role_names = [123]

            if parsed.exclude:
                excluded_role_names = parsed.exclude
            else:
                excluded_role_names = None

        results: Set[discord.Member] = set()

        if role_names is None:
            raise errors.MissingArgumentError(
                message="You must specify a role to search for.",
                argument_name="role_name",
            )
            return

        if role_names == [123]:
            results = set(ctx.bot.guild.members)
            roles_search = None

        else:
            roles_search: List[discord.Role] = [
                self.get_role_by_name(role_name) for role_name in role_names
            ]
            for role in roles_search:
                if len(results) == 0:
                    results.update(self.get_role_members(role))
                else:
                    results = results.intersection(self.get_role_members(role))

        if excluded_role_names is not None:
            roles_excluded: List[discord.Role] = [
                self.get_role_by_name(role_name) for role_name in excluded_role_names
            ]
            for role in roles_excluded:
                results.difference_update(self.get_role_members(role))

        if not results:
            raise errors.MemberNotFoundError(
                message="No members were found with your specified criteria."
            )
            return

        # Sort the results by display_name
        member_names = sorted(results, key=lambda m: m.display_name.lower())
        member_str = "\n".join(member.name for member in member_names)
        role_or_roles = (
            "role" if role_names == [123] or len(roles_search) == 1 else "roles"
        )
        role_or_roles_x = (
            "role"
            if excluded_role_names is None or len(roles_excluded) == 1
            else "roles"
        )

        role_names_we_searched = (
            role_or_roles
            + " "
            + ", ".join(
                [
                    "`" + self.remove_name_decoration(role.name) + "`"
                    for role in roles_search
                ]
            )
            if roles_search
            else ""
        )

        await ctx.send(
            f"Here are the {len(member_names)} people with the {role_names_we_searched}"
            + f"{' and the ' if role_names != [123] and excluded_role_names else ''}{'excluded ' + role_or_roles_x + ' ' if excluded_role_names else ''}"
            + f"{', '.join(['`'+self.remove_name_decoration(role.name)+'`' for role in roles_excluded]) if excluded_role_names else ''}:"
        )
        await send_long(ctx.channel, member_str, code_block=True)

    @checks.is_team_bot_channel(slash_cmd=True)
    @checks.app_cmd_check_any(
        checks.is_dev_team(True), checks.is_team_lead(True), checks.is_white_shirt(True)
    )
    @app_commands.command(
        name="rtv", description="Returns a list of members having the role"
    )
    @app_commands.guilds(discord.Object(id=settings.SERVER_ID))
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(role="list the members of this role")
    async def rtv_slash(self, di: discord.Interaction, role: discord.Role):
        try:
            results = self.get_role_members(role)
        except errors.GetRoleMembersError:
            await interaction_reply(di, f"`{role.name}` role has no members")
            return
        member_names = sorted(results, key=lambda m: m.display_name.lower())
        member_str = "\n".join(member.name for member in member_names)
        await interaction_reply(
            di, f"Here are the {len(member_names)} people with `{role.name}`'s role"
        )
        await send_long(di.channel, member_str, code_block=True)

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.hybrid_command(
        name="count_officers", description="count officers in each ranks"
    )
    @app_commands.guilds(discord.Object(id=settings.SERVER_ID))
    async def count_officers(self, ctx):
        """
        This command returns an embed with a count of all officers by rank,
        as well as a total count.
        """

        # For every rank in settings.ROLE_LADDER, get the number of members with the role having that rank.id
        # Then add that to a dictionary with the role name as the key, and the number of members as the value.

        # Create a dictionary of all the roles and their corresponding member count
        # This will be used to create the embed later.
        # The keys are the role names, and the values are the member count.

        all_officer_count = len(ctx.bot.guild.get_role(settings.LPD_ROLE).members)

        # Create an embed to send to the channel
        embed = discord.Embed(
            title="Number of all LPD Officers: " + str(all_officer_count),
            colour=discord.Colour.dark_green(),
        )

        for rank in settings.ROLE_LADDER.__dict__.values():
            role: Optional[discord.Role] = ctx.bot.guild.get_role(rank.id)
            if role is None:
                log.error(f"{rank.name=} [{rank.id}] not found!")
                continue

            rank_name = self.remove_name_decoration(role.name)
            if rank_name == "Cadet":
                rank_name = "LPD " + rank_name

            embed.add_field(
                name=rank_name,
                value="**"
                + str(len(role.members))
                + "**"
                + " ("
                + str(round(100 * len(role.members) / all_officer_count, 2))
                + "%)",
                inline=True,
            )

        await ctx.send(embed=embed)

    @checks.is_team_bot_channel(slash_cmd=True)
    @checks.app_cmd_check_any(
        checks.is_any_trainer(True),
        checks.is_event_host(True),
        checks.is_white_shirt(True),
    )
    @app_commands.command(
        name="who", description="Returns a list of officers currently patroling"
    )
    @app_commands.guilds(discord.Object(id=settings.SERVER_ID))
    @app_commands.default_permissions(administrator=True)
    async def who(
        self,
        di: discord.Interaction,
        list_type: Literal["All", "Patrol", "Training"],
    ):
        r = self.bl_wrapper.pt_bl.get_patrolling_officers()

        def custom_sort_key(channel_name):
            if channel_name.startswith("CO"):
                return (3, channel_name)
            elif channel_name.startswith("LMT"):
                return (2, channel_name)
            elif channel_name.startswith("SLRT"):
                return (1, channel_name)
            elif "dispatch" in channel_name.lower():
                return (-1, channel_name)
            else:
                return (0, channel_name)

        voice_channels = [self.bot.get_channel(channel_id) for channel_id in r.keys()]
        if list_type != "All":
            for vc in voice_channels.copy():
                if (
                    list_type == "Patrol"
                    and "Training" in vc.name
                    or list_type == "Training"
                    and "Training" not in vc.name
                ):
                    voice_channels.remove(vc)

        sorted_channels = sorted(
            voice_channels, key=lambda item: custom_sort_key(item.name)
        )

        message = "Template:\n```\nEvent Host:\nDispatch:\nGroup Leads:\n\n"
        for channel in sorted_channels:
            officers = r[channel.id]
            message += f"\n** {channel.name} **:\n"
            message += "".join([f"<@{o}>\n" for o in officers])
        message += "```"
        await interaction_send_long(di, message)

    @checks.is_team_bot_channel(slash_cmd=True)
    @checks.app_cmd_check_any(
        checks.is_event_host(True),
        checks.is_white_shirt(True),
    )
    @app_commands.command(
        name="get_schedule_template",
        description="Get a template for the schedule of the week",
    )
    @app_commands.guilds(discord.Object(id=settings.SERVER_ID))
    @app_commands.default_permissions(administrator=True)
    async def get_schedule_template(
        self,
        di: discord.Interaction,
        list_type: Literal["All", "On Duty Events", "Off Duty Events"],
        week_number: Optional[int],
        year: Optional[int],
    ):
        msg_lines = []
        today = dt.datetime.now(tz=dt.timezone.utc)
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        if year is None:
            year = today.year
        if week_number is None:
            week_number = today.isocalendar()[1] + 1

        start_dt = get_monday_from_week(year, week_number)
        end_dt = start_dt + dt.timedelta(days=6)

        filter = list_type
        type_name = filter
        if list_type == "All":
            type_name = "Events"
            filter = None

        if list_type != "Off Duty Events":
            msg_lines.append(settings.SCHEDULE_TEMPLATE_HEADER_ON_DUTY)

        if start_dt.month != end_dt.month:
            msg_lines.append(
                f"# **LPD {type_name.upper()}: {start_dt.strftime('%B %d').upper()} - {end_dt.strftime('%B %d').upper()}**"
            )
        else:
            msg_lines.append(
                f"# **LPD {type_name.upper()}: {start_dt.strftime('%B %d').upper()}-{end_dt.day}**"
            )

        na_time = start_dt.replace(tzinfo=ZoneInfo("America/Los_Angeles"))
        eu_time = start_dt.replace(tzinfo=ZoneInfo("Europe/London"))
        # as_time = start_dt.replace(tzinfo=ZoneInfo("Australia/Brisbane"))
        if na_time.dst() != eu_time.dst():
            msg_lines.append(
                "## :warning: Daylight saving is in transition period\nSome countries enable daylight saving at different dates which could lead to incorrect time here or on Teamup.\n**The ground truth is when the event is announced.**\n"
            )

        events = await get_calendar_events(filter, year, week_number)
        if len(events) == 0:
            msg_lines.append(":red_circle: no events found")

        def print_event(component, startOverride=None) -> str:
            event_start = component.get("DTSTART").dt
            event_end = component.get("DTEND").dt
            if startOverride:
                event_end = startOverride + (event_end - event_start)
                event_start = startOverride

            title = ""
            # yeap calendar entries are broken, seems they mostly use description for normal on duty and summary for off
            # if "DESCRIPTION" in component and (
            #     "Off Duty" not in component.get("CATEGORIES").to_ical().decode()
            # ):
            #     title = "\n".join(component.get("DESCRIPTION").split("\n")[2:3])
            #     if title.startswith("Who: "):
            #         title = title[5:]
            #     if title.startswith("Host: "):
            #         title = title[6:]
            # if len(title) == 0:
            title = component.get("SUMMARY").split("\n")[0]
            if "X-TEAMUP-WHO" in component:
                title = title[: -(len(component.get("X-TEAMUP-WHO")) + 2)]

            # s = f"**{title}** - {component.get('CATEGORIES').to_ical().decode().replace(filter,'')}\n"
            s = f"**{title}**\n"
            if isinstance(event_start, dt.datetime):
                if "X-TEAMUP-WHO" in component:
                    s += f"**Hosted By:** @{component.get('X-TEAMUP-WHO')}\n"
                else:
                    s += "**Hosted By:** TBA\n"
                s += f"**Time:** <t:{int(event_start.timestamp())}:F>"
            else:
                s += f"**Time:** <t:{int(dt.datetime.combine(event_start, dt.time(0,0)).timestamp())}:D> to <t:{int(dt.datetime.combine(event_end, dt.time(12,0)).timestamp())}:D>"

            # dump debug
            # s += "\n"
            # for k, v in component.items():
            #     if k == "CATEGORIES":
            #         s += f"[{k}] = {v.to_ical().decode()}\n"
            #     else:
            #         s += f"[{k}] = {v}\n"

            return s

        for k in sorted(events.keys()):
            if isinstance(events[k], list):
                msg_lines.append(print_event(events[k][0], events[k][1]))
            else:
                msg_lines.append(print_event(events[k]))

        if list_type == "Off Duty Events":
            msg_lines.append(settings.SCHEDULE_TEMPLATE_FOOTER_OFF_DUTY)
        else:
            msg_lines.append(
                settings.SCHEDULE_TEMPLATE_FOOTER_ON_DUTY.replace(
                    "%BOT_ID%",
                    str(self.bot.application_id),
                )
            )

        await interaction_send_long(di, "\n\n".join(msg_lines), code_block=True)

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_commands.command(
        name="member_lookup", description="gives top patrolling times"
    )
    @app_commands.guilds(discord.Object(id=settings.SERVER_ID))
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(search="discord id, username discord/vrchat")
    async def member_lookup(
        self,
        interac: discord.Interaction,
        search: str,
    ):
        result = await self.bl_wrapper.mm_bl.member_lookup(search)
        await interaction_send_long(interac, result)


async def setup(bot):
    await bot.add_cog(Other(bot))
