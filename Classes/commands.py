# Standard
import sys
from copy import deepcopy
import argparse
import re
from io import StringIO, BytesIO
from datetime import datetime, timedelta, timezone, time
import time
import math
import traceback
import json
import aiomysql
import asyncio

# Community
import discord
from discord.ext import commands
import texttable
import arrow

# Mine
from Classes.extra_functions import send_long, handle_error, get_rank_id, has_role
from Classes.custom_arg_parse import ArgumentParser
from Classes.menus import Confirm
import Classes.errors as errors
import Classes.checks as checks
from Classes.extra_functions import role_id_index, get_role_name_by_id
from Classes.VRChatListener import add_officer_as_friend, join_user

class Time(commands.Cog):
    """Here are all the commands relating to managing the time of officers."""

    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.blue()

    # Time functions

    @staticmethod
    def seconds_to_string(seconds, max_values=0, multi_line=False):
        """
        This function takes in seconds and returns a string that represents it with seconds,
        minutes, hours, days and weeks, it can be adjusted how many of these you want to see.

        Args:

            seconds (int): How many seconds should be calculated into a string.

            max_values (int, optional): How many values should be displayed, this can go from 0-5, 0 means that it will show as many as possible. For example with two it would only show minutes and seconds. Defaults to 0.

            multi_line (bool, optional): Allow the returned string to span multiple lines. Defaults to True.

        Raises:

            ValueError: If max_values is under 0 or above 5.

        Returns:

            string: This string represents the seconds passed in in a human readable fromat.
        """

        # Check on the value of max_values
        max_value = 5
        if max_values > max_value or max_values < 0:
            raise ValueError(f"max_values can't be higher than {max_value}.")
        elif max_values == 0:
            max_values = max_value

        # Calculate weeks, days, hours, minutes and seconds.
        # This is the code that is commented out below but translated into a for loop.
        divisions = [60, 60, 24, 7]
        calculations = [[seconds]]
        for i in range(0, len(divisions)):
            second_if_end, first = divmod(calculations[i][0], divisions[i])
            calculations[i].append(first)
            calculations.append([second_if_end])
        # Old Code:
        # seconds_if_end = seconds
        # minutes_if_end, seconds = divmod(seconds_if_end, 60)
        # hours_if_end, minutes = divmod(minutes_if_end, 60)
        # days_if_end, hours = divmod(hours_if_end, 24)
        # weeks_if_end, days = divmod(days_if_end, 7)

        # # Set up the list
        # calculations = [
        #     [seconds_if_end, seconds],
        #     [minutes_if_end, minutes],
        #     [hours_if_end,   hours],
        #     [days_if_end,    days],
        #     [weeks_if_end]
        # ]
        # print(calculations)

        # Move the time to the string
        return_str = ""
        time_names = ["Seconds", "Minutes", "Hours", "Days", "Weeks"]
        for i in range(0, max_values):

            # Determine the fetch num
            if i + 1 == max_values:
                fetch_num = 0
            else:
                fetch_num = 1

            # Add to the string
            if multi_line:
                # End the loop if everything after will be 0
                if calculations[i][0] == 0 and i != 0:
                    break
                return_str = (
                    f"{time_names[i]}: {calculations[i][fetch_num]}\n{return_str}"
                )
            else:
                if i == 0:
                    return_str = f"{calculations[i][fetch_num]}"
                else:
                    return_str = f"{calculations[i][fetch_num]}:{return_str}"

        # Return the string
        return return_str

    def get_officer_id(self, officer_string):

        # Check for an @ mention
        p = re.compile(r"<@\![0-9]+>")
        match = p.match(officer_string)
        if match:
            return int(match.group()[3:-1])

        # Check for an ID
        p = re.compile(r"[0-9]+")
        match = p.match(officer_string)
        if match:
            return int(match.group())

        # Nothing was found
        return None

    def create_last_active_embed(self, officer, time_results):

        if not time_results:
            embed = discord.Embed(description="No activity recorded")
        else:
            embed = discord.Embed(description="Latest activity")

        # Set the author of the embed
        embed.set_author(name=officer.display_name, icon_url=officer.member.avatar_url)

        # Return the embed if their are no results to add
        if not time_results:
            return embed

        # Order the time_results:
        time_results = sorted(
            time_results, key=lambda x: time.mktime(x["time"].timetuple()), reverse=True
        )

        # Add the channels
        for result in time_results:
            if result["channel_id"] == None:
                embed.add_field(
                    name=arrow.Arrow.fromdatetime(result["time"]).humanize(),
                    value=result["other_activity"],
                )
            else:
                url = f"https://discordapp.com/channels/{self.bot.officer_manager.guild.id}/{result['channel_id']}/{result['message_id']}"
                embed.add_field(
                    name=arrow.Arrow.fromdatetime(result["time"]).humanize(),
                    value=f"[#{self.bot.get_channel(result['channel_id']).name}]({url})",
                )

        return embed

    @staticmethod
    def parse_date(date_string):
        date = date_string.split("/")

        # Make sure the length is correct
        if len(date) != 3:
            raise ValueError(
                "Their is an error in the date you put in, make sure to split the date with a slash. Example: 30/2/2020"
            )

        # Convert everything into numbers
        date = [int(i) for i in date]

        return datetime(date[2], date[1], date[0])

    def parse_days_date_input(self, parsed):

        # ====================
        # Parse extra options
        # ====================

        # Set the variables
        from_datetime = None
        to_datetime = None
        time_string = None

        # The user selected nothing and will get the automatic option
        if parsed.days == None and parsed.from_date == None and parsed.to_date == None:
            parsed.days = 28

        # The user selected a set amount of days
        if parsed.days != None:

            # Create the datetime objects from the number of second since epoc
            from_datetime = datetime.fromtimestamp(
                math.floor(time.time() - parsed.days * 86400)
            )
            to_datetime = datetime.fromtimestamp(math.floor(time.time()))

            time_string = f"for the last {parsed.days} days"

        # The user selected from or to dates
        elif parsed.from_date != None or parsed.to_date != None:

            if parsed.from_date == None and parsed.to_date != None:
                # The user is giving to_time and thus wants from_time
                # to be a month before from_time
                to_datetime = self.parse_date(parsed.to_date)
                from_datetime = to_datetime - timedelta(days=28)

            elif parsed.from_date != None and parsed.to_date == None:
                # The user is giving from_time and thus wants from_time
                # to be the current time
                from_datetime = self.parse_date(parsed.from_date)
                to_datetime = datetime.now(timezone.utc)

            else:
                # Both are here, they can just be parsed
                from_datetime = self.parse_date(parsed.from_date)
                to_datetime = self.parse_date(parsed.to_date)

            # Set the out_string to store the first part of the message to the user
            time_string = f'from: {from_datetime.strftime("%d/%m/%Y")}  to: {to_datetime.strftime("%d/%m/%Y")}'

        return (time_string, from_datetime, to_datetime)

    # Commands

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command(usage="[options] <officer>")
    async def patrol_time(self, ctx, *args):
        """
        This command gets the on duty time for an officer.


        OPTIONS

            -d NUMBER,
            --days NUMBER
                specify the number of days to look back for activity, this defaults to 28.

            -f DATE,
            --from-date DATE
                specify the date to look back at, if no --to-date is specified it will show all activity from the --from-date to right now.

            -t DATE,
            --to-date DATE
                specify the date to stop looking at, --from-date has to be specified with this option.

            -l,
            --list
                get a list of all patrols during the specified time period.

        PARSE RAW
        """

        # Setup parser
        parser = ArgumentParser(description="Argparse user command")
        parser.add_argument("officer")
        parser.add_argument("-d", "--days", type=int)
        parser.add_argument("-f", "--from-date")
        parser.add_argument("-t", "--to-date")
        parser.add_argument("-l", "--list", action="store_true")

        # Parse command and check errors
        try:
            parsed = parser.parse_args("=patrol_time", args)
        except argparse.ArgumentError as error:
            await ctx.send(ctx.author.mention + " " + str(error))
            return
        except argparse.ArgumentTypeError as error:
            await ctx.send(ctx.author.mention + " " + str(error))
            return
        except errors.ArgumentParsingError as error:
            await ctx.send(ctx.author.mention + " " + str(error))
            return

        # Get the officer ID
        officer_id = self.get_officer_id(parsed.officer)
        if officer_id == None:
            ctx.send("Make sure to mention an officer.")
            return
        print(f"officer_id: {officer_id}")

        # Make sure the person mentioned is an LPD officer
        officer = self.bot.officer_manager.get_officer(officer_id)
        if officer is None:
            await ctx.send(
                "The person you mentioned is not being monitored, are you sure this person is an officer?"
            )
            return

        # ====================
        # Get the datetime
        # ====================

        try:
            time_text, from_datetime, to_datetime = self.parse_days_date_input(parsed)
        except ValueError as error:
            ctx.send(error)
            return
        out_string = f"On duty time for {officer.mention} - {time_text}"

        # ====================
        # Output
        # ====================

        if not parsed.list:

            # Get the time in seconds
            time_seconds = await officer.get_time(from_datetime, to_datetime)

            # Print the results out
            out_string += "\n" + self.seconds_to_string(time_seconds, multi_line=True)
            await ctx.send(out_string)

        else:

            # Get all the patrols
            all_patrols = await officer.get_full_time(from_datetime, to_datetime)

            # Send the header
            await ctx.send(out_string)
            out_string = ""

            # Set up the header of the table
            table = texttable.Texttable()
            table.header(["From      ", "To        ", "hr:min:sec"])

            # This is a lambda to add the discord code block on the table to keep it monospace
            draw_table = lambda table: "```\n" + table.draw() + "\n```"

            # Loop through all the patrols to add them to a string and send them
            for patrol in all_patrols:

                # Store the old table in case the new one gets too long
                old_table = draw_table(table)

                # This is the timeformat the tables will show
                time_format = "%d/%m/%Y"

                # Add the next row
                table.add_row(
                    [
                        str(patrol[0].strftime(time_format)),
                        str(patrol[1].strftime(time_format)),
                        str(self.seconds_to_string(patrol[2], max_values=3)),
                    ]
                )

                # This executes if the table is too long to be sent in one discord message
                if len(draw_table(table)) >= 2000:

                    # Send the old table because the new one is too long to send
                    await ctx.send(old_table)

                    # Create a new table and add the current row to it
                    table = texttable.Texttable()
                    table.add_row(
                        [
                            str(patrol[0].strftime(time_format)),
                            str(patrol[1].strftime(time_format)),
                            str(patrol[2]),
                        ]
                    )

            # Send the table if it is not empty
            if len(table.draw()) > 0:
                await ctx.send(draw_table(table))

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command()
    async def last_active(self, ctx, officer):
        """
        This command gets all the times the officer was last active.

        To use the command do =last_active_time @mention_the_officer_or_officer_id,
        for example =last_active_time @Hroi#1994 or =last_active_time 378666988412731404.
        """

        officer_id = self.get_officer_id(officer)
        if officer_id == None:
            ctx.send("Make sure to mention an officer.")
            return
        print(f"officer_id: {officer_id}")

        # Make sure the person mentioned is an LPD officer
        officer = self.bot.officer_manager.get_officer(officer_id)
        if officer is None:
            await ctx.send(
                "The person you mentioned is not being monitored, are you sure this person is an officer?"
            )
            return

        # Get the time
        result = await officer.get_all_activity(
            ctx.bot.officer_manager.all_monitored_channels
        )

        # Send the embed
        await ctx.send(embed=self.create_last_active_embed(officer, result))

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command(usage="[options] <how_many_officers>")
    async def top(self, ctx, *args):
        """
        This command gets a list of officers ordered by their activity.


        OPTIONS

            -d NUMBER,
            --days NUMBER
                specify the number of days to look back for activity, this defaults to 28.

            -f DATE,
            --from-date DATE
                specify the date to look back at, if no --to-date is specified it will show all activity from the --from-date to right now.

            -t DATE,
            --to-date DATE
                specify the date to stop looking at, --from-date has to be specified with this option.

        PARSE RAW
        """

        # Setup parser
        parser = ArgumentParser(description="Argparse user command")
        parser.add_argument("how_many_officers", type=int)
        parser.add_argument("-d", "--days", type=int)
        parser.add_argument("-f", "--from-date")
        parser.add_argument("-t", "--to-date")

        # Parse command and check errors
        try:
            parsed = parser.parse_args("=top", args)
        except argparse.ArgumentError as error:
            await ctx.send(ctx.author.mention + " " + str(error))
            return None
        except argparse.ArgumentTypeError as error:
            await ctx.send(ctx.author.mention + " " + str(error))
            return
        except errors.ArgumentParsingError as error:
            await ctx.send(ctx.author.mention + " " + str(error))
            return

        # Parse the day input
        try:
            time_text, from_datetime, to_datetime = self.parse_days_date_input(parsed)
        except ValueError as error:
            ctx.send(error)
            return

        # Get the time for all the officers
        all_times = await self.bot.officer_manager.get_most_active_officers(
            from_datetime, to_datetime, limit=parsed.how_many_officers
        )

        # Format the output and send it
        output_list = []
        output_list.append(f"Top on duty times - {time_text}:")
        output_list.append("Officer | On duty time")
        for officer_result in all_times:
            officer = self.bot.officer_manager.get_officer(officer_result[0])
            time_string = self.seconds_to_string(officer_result[1])

            output_list.append(f"{officer.mention} | {time_string}")

        await send_long(ctx.channel, "\n".join(output_list))

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command()
    async def officer_promotions(self, ctx, required_hours):
        """
        This command lists all the recruits that have been active enough in the last 28 
        days to get promoted to officer.
        """

        # Make sure required_hours is a number
        try:
            required_hours = int(required_hours)
        except ValueError:
            await ctx.send("required_hours needs to be a number.")
            return

        # Get everyone that has been active enough
        all_times = await self.bot.officer_manager.get_most_active_officers(
            datetime.now(timezone.utc) - timedelta(days=28),
            datetime.now(timezone.utc),
            limit=None,
        )

        # Filter list for only recruits that have been active enough
        all_officers_for_promotion = []
        for row in all_times:
            officer = self.bot.officer_manager.get_officer(row[0])

            recruit_role_id = self.bot.officer_manager.get_settings_role("recruit")[
                "id"
            ]
            if (
                officer
                and recruit_role_id in (x.id for x in officer.member.roles)
                and row[1] >= required_hours * 3600
            ):
                all_officers_for_promotion.append(officer)

        # Format the output and send it
        if len(all_officers_for_promotion) == 0:
            await ctx.send(
                f"Their are no recruits that have been active for {required_hours} hours in the last 28 days."
            )
        else:
            out_str = "\n".join(
                (
                    f"Recruits that have been active for {required_hours} hours in the last 28 days:",
                    "\n".join(f"@{x.discord_name}" for x in all_officers_for_promotion),
                )
            )
            await send_long(ctx.channel, out_str)

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command(usage="<officers_to_promote>")
    async def promote_to_officer(self, ctx, *args):
        """
        This command promotes everyone that is mentioned in the message to officer.

        This command should be used after =officer_promotions, when everyone has agreed
        on who should be promoted and the promotion message has been posted in
        #announcements.

        You can just paste the message that came from =officer_promotions into this
        command as long as everyone agreed that their was no one that needed to be
        removed from that list.
        """

        # Make sure the admin is sure
        result = await Confirm(
            "Are you sure you want to promote all the recruits you mentioned to officer?"
        ).prompt(ctx)
        if result != True:
            await ctx.send("The promotion has been cancelled.")
            return

        # Set up some global variables
        guild = self.bot.officer_manager.guild
        recruit_role = guild.get_role(
            self.bot.officer_manager.get_settings_role("recruit")["id"]
        )
        officer_role = guild.get_role(
            self.bot.officer_manager.get_settings_role("officer")["id"]
        )

        # Promote everyone
        try:

            await ctx.send("I am now promoting everyone, please give me a few minutes.")

            for member in ctx.message.mentions:
                # Make sure the officer is a recruit
                if recruit_role.id in (x.id for x in member.roles):
                    await member.add_roles(officer_role)
                    await member.remove_roles(recruit_role)

            await ctx.send("Everyone has been promoted to officer successfully.")

        except Exception as error:
            await ctx.send(
                "**Not everyone was promoted to officer successfully**. Please go through and manually change the roles of members that did not get promoted. Please also contact Hroi so that he can fix the bot before next officer promotions happen."
            )
            await handle_error(ctx.bot, error, traceback.format_exc())

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command()
    async def remove_inactive_cadets(self, ctx, inactive_days_required):
        """
        This command removes all cadets that have been inactive for 
        28 days.
        """

        # Make sure inactive_days_required is an integer
        try:
            inactive_days_required = int(inactive_days_required)
        except ValueError:
            await ctx.send("inactive_days_required needs to be a whole number.")
            return

        # Make sure the user is sure.
        are_you_sure = await Confirm(
            f"Are you sure you want to remove all cadets that have been inactive for {inactive_days_required} days?",
            delete_message_after=False,
            clear_reactions_after=True,
        ).prompt(ctx)
        if not are_you_sure:
            await ctx.send("Cadet removal has been canceled.")
            return

        await ctx.send("Please give me a moment to find all the inactive cadets.")

        # Create a list of who needs to be removed
        officers_to_remove = []
        cadet_id = get_rank_id(self.bot.settings, "cadet")
        cadets = (
            c
            for c in self.bot.officer_manager.guild.members
            if has_role(c.roles, cadet_id)
        )
        for cadet in cadets:

            # Get the officer
            officer = self.bot.officer_manager.get_officer(cadet.id)
            if not officer:
                await ctx.send(
                    f"WARNING {cadet.mention} is a cadet but is not being monitored."
                )
                continue

            # Check the last activity
            last_activity = await officer.get_last_activity(
                ctx.bot.officer_manager.all_monitored_channels
            )
            active_days_ago = (datetime.now() - last_activity["time"]).days
            if active_days_ago > inactive_days_required:
                officers_to_remove.append(officer)

        # Check if their are no cadets to remove
        if len(officers_to_remove) == 0:
            await ctx.send(
                f"{ctx.author.mention} Their are no inactive cadets to remove."
            )
            return

        # Make sure the user is sure again
        officers_to_remove_str = "\n".join((x.mention for x in officers_to_remove))
        await send_long(
            ctx.channel,
            f"Here is everyone that will be removed:\n{officers_to_remove_str}",
        )
        are_you_sure = await Confirm(
            f"{ctx.author.mention} Are you sure you want to remove all these cadets?",
            timeout=300,
            delete_message_after=False,
            clear_reactions_after=True,
        ).prompt(ctx)
        if not are_you_sure:
            await ctx.send("Cadet removal has been canceled.")
            return

        # Start the removal process
        await ctx.send("Please give me a moment again, this may take quite some time.")
        # Get the roles to be updated
        lpd_role = self.bot.officer_manager.guild.get_role(
            self.bot.settings["lpd_role"]
        )
        cadet_role = self.bot.officer_manager.guild.get_role(
            get_rank_id(self.bot.settings, "cadet")
        )
        for officer in officers_to_remove:

            # Update the roles
            try:
                await officer.member.remove_roles(lpd_role, cadet_role)
            except discord.HTTPException as error:
                await ctx.send(f"WARNING Failed to remove {officer.mention}")
                await handle_error(self.bot, error, traceback.format_exc())

        await ctx.send(
            f"{ctx.author.mention} I have now removed all the inactive cadets."
        )


class VRChatAccoutLink(commands.Cog):
    """This stores all the VRChatAccoutLink commands."""

    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.red()

    @commands.command()
    @checks.is_lpd()
    @checks.is_general_bot_channel()
    async def info(self, ctx):
        """
        This command gets info about your current account status.

        This command shows you information about if you have your VRChat account connected or
        not and how to connect it or disconnect it.
        """
        vrchat_name = self.bot.user_manager.get_vrc_by_discord(ctx.author.id)
        if vrchat_name:
            await ctx.send(
                f"You have a VRChat account linked with the name `{vrchat_name}`, if you want to unlink it use the command =unlink or if you want to update your VRChat name use the command =link new_vrchat_name."
            )
        else:
            await ctx.send(
                "You do not have a VRChat account linked, to connect your VRChat account do =link your_vrchat_name."
            )

    @commands.command()
    @checks.is_lpd()
    @checks.is_general_bot_channel()
    async def link(self, ctx, vrchat_name):
        r"""
        This command is used to tell the bot your VRChat name.
        
        When you successfully link your VRChat account with the bot,
        you will receive a friend request from LPD Officer Monitor.
        Please accept this friend request as soon as possible, to
        ensure the most accurate logging of on-duty time.

        This information is used for detecting if you are in
        the LPD when entering the LPD Station. To use the
        command do =link your_vrchat_name.

        If your VRChat name contains spaces put quotes before and after
        your VRChat name, example: =link "your vrchat name". If it contains
        quotes and spaces you can do \ before every quote you want to be
        apart of your name, example: =link "your \\\"vrchat\\\" name".

        If your name contains any special characters like symbols make sure to
        copy your VRChat name from the debug console in the LPD Station. The
        debug console can be enabled with a button under the front desk.
        """

        # Make sure the name does not contain the seperation character
        if self.bot.settings["name_separator"] in vrchat_name:
            hroi = self.bot.get_guild(self.bot.settings["Server_ID"]).get_member(
                378666988412731404
            )
            await ctx.send(
                f'The name you put in contains a character that cannot be used "{self.bot.settings["name_separator"]}" please change your name or contact {hroi.mention} so that he can change the illegal character.'
            )
            return

        # If the officer already has a registered account
        previous_vrchat_name = self.bot.user_manager.get_vrc_by_discord(ctx.author.id)
        if previous_vrchat_name:
            confirm = await Confirm(
                f"You already have a VRChat account registered witch is `{previous_vrchat_name}`, do you want to replace that account?"
            ).prompt(ctx)
            if not confirm:
                await ctx.send(
                    "Your account linking has been cancelled, if you did not intend to cancel the linking you can use the command =link again."
                )
                return

        # Confirm the VRC name
        confirm = await Confirm(
            f"Are you sure `{self.bot.user_manager.vrc_name_format(vrchat_name)}` is your full VRChat name?\n**You will be held responsible of the actions of the VRChat user with this name.**"
        ).prompt(ctx)
        if confirm:
            await self.bot.user_manager.add_user(ctx.author.id, vrchat_name)
            await ctx.send(
                f"Your VRChat name has been set to `{vrchat_name}`\nIf you want to unlink it you can use the command =unlink\nPlease check your VRChat incoming friend requests for a request from `{settings['VRC_Username']}`. This will ensure correct logging of on-duty time."
            )
        else:
            await ctx.send(
                "Your account linking has been cancelled, if you did not intend to cancel the linking you can use the command =link again."
            )
            return
        
        await add_officer_as_friend(vrchat_name)

    @commands.command()
    @checks.is_lpd()
    @checks.is_general_bot_channel()
    async def unlink(self, ctx):
        """
        This command removes your account if you have a
        connected VRChat account.
        """
        vrchat_name = self.bot.user_manager.get_vrc_by_discord(ctx.author.id)

        if vrchat_name == None:
            await ctx.send("You do not have your VRChat name linked.")
            return

        confirm = await Confirm(
            f"Your VRChat name is currently set to `{vrchat_name}`. Do you want to unlink that?"
        ).prompt(ctx)
        if confirm:
            await self.bot.user_manager.remove_user(ctx.author.id)
            await ctx.send(
                "Your VRChat name has been successfully unlinked, if you want to link another account you can do that with =link."
            )
        else:
            await ctx.send(
                f"Your VRChat accout has not been unlinked and is still `{vrchat_name}`"
            )

    @commands.command()
    @checks.is_team_bot_channel()
    @commands.check_any(checks.is_white_shirt(), checks.is_dev_team())
    async def lvn(self, ctx):
        """
        This command is used to get the VRChat names of the people that are LPD Officers.

        The output from this command is only intended to be read by computers and is not
        easy to read for humans.
        """
        sep_char = self.bot.settings["name_separator"]
        vrc_names = [x[1] for x in self.bot.user_manager.all_users]

        output_text = f"{sep_char.join(vrc_names)}"
        if len(output_text) == 0:
            await ctx.send("There are no registered users.")
        else:
            await send_long(ctx.channel, output_text, code_block=True)

    @commands.command()
    @checks.is_white_shirt()
    @checks.is_admin_bot_channel()
    async def list(self, ctx):
        """
        This command shows the Discord and VRChat names of all officers registered with the bot.

        This information is intended to check who has a specific VRChat account.
        """
        out_string = "**All linked accounts:**\n**Discord - VRChat\n**"

        guild = self.bot.get_guild(self.bot.settings["Server_ID"])
        for user in self.bot.user_manager.all_users:
            member = guild.get_member(user[0])
            string_being_added = f"`{member.display_name} - {user[1]}`\n"

            if len(out_string + string_being_added) >= 2000:
                await ctx.send(out_string)
                out_string = string_being_added
            else:
                out_string += string_being_added
        await ctx.send(out_string)

    @commands.command()
    @checks.is_white_shirt()
    @checks.is_admin_bot_channel()
    async def debug(self, ctx):
        """
        This command is just for testing the bot.
        """
        await ctx.send(str(self.bot.user_manager.all_users))


class Applications(commands.Cog):
    """Here are all the commands relating to managing the applications."""

    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.orange()

    @checks.is_application_channel()
    @checks.is_recruiter()
    @commands.command(usage="<mentioned_officers>")
    async def add(self, ctx, *args):
        """
        This command adds the recruit and LPD roles to the members you mention.
        It also removes the civilian role when needed.
        """
        result = await Confirm(
            "Are you sure you want to add all the members you mentioned to the LPD?"
        ).prompt(ctx)
        if not result:
            await ctx.send("Officer adding canceled.")
        else:
            # Store the bots messages
            bot_messages = []

            # Update the roles for all the members
            bot_messages.append(
                await ctx.send(
                    "Please give me one moment while I update everyone's roles."
                )
            )
            for member in ctx.message.mentions:
                # Make sure the member is not an officer already
                if self.bot.officer_manager.is_officer(member):
                    bot_messages.append(
                        await ctx.send(
                            f"{member.mention} is already an officer and has been skipped."
                        )
                    )
                    continue

                # Get the roles to be updated
                lpd_role = self.bot.officer_manager.guild.get_role(
                    self.bot.settings["lpd_role"]
                )
                cadet_role = self.bot.officer_manager.guild.get_role(
                    get_rank_id(self.bot.settings, "cadet")
                )

                # Update the roles
                await member.add_roles(lpd_role, cadet_role)
            bot_messages.append(
                await ctx.send("Everyone you mentioned has been added to cadet.")
            )

            # Remove the users message
            result = await Confirm("Can I remove your message?").prompt(ctx)
            if result:
                await ctx.message.delete()

            # Remove all the bot messages
            for message in bot_messages:
                await message.delete()


class Other(commands.Cog):
    """Here are all the one off commands that I have created and are not apart of any group."""

    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.dark_magenta()
        self.get_vrc_name = (
            lambda x: self.bot.user_manager.get_vrc_by_discord(x.id) or x.display_name
        )

    def get_role_by_name(self, role_name):

        # Get the role
        for role in self.bot.officer_manager.guild.roles:
            if self.filter_start_end(role.name, ["|", " ", "⠀", " "]) == role_name:
                return role

        raise errors.GetRoleMembersError(message=f"The role {role_name} was not found.")

    def get_role_members(self, role):

        # Make sure that people have the role
        if not role.members:
            raise errors.GetRoleMembersError(message=f"{role_name} is empty.")

        # Sort the members
        return sorted(role.members, key=self.get_vrc_name)

    @staticmethod
    def filter_start_end(string, list_of_characters_to_filter):
        while True:
            if string[0] in list_of_characters_to_filter:
                string = string[1::]
            else:
                break

        while True:
            if string[-1] in list_of_characters_to_filter:
                string = string[0:-1]
            else:
                break

        return string

    @checks.is_team_bot_channel()
    @commands.check_any(checks.is_white_shirt(), checks.is_dev_team())
    @commands.command()
    async def rtv(self, ctx, role_name):
        """
        This command takes in a name of a role and outputs the VRC names of the people in it.

        This command ignores the decoration on the role if it has any and it also requires
        """

        try:
            members = self.get_role_members(self.get_role_by_name(role_name))
        except errors.GetRoleMembersError as error:
            await ctx.send(error)
            return

        members_str = "\n".join(self.get_vrc_name(x) for x in members)

        # Send everyone
        await ctx.send(f"Here is everyone in the role {role_name}:")
        await send_long(ctx.channel, members_str, code_block=True)

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    # @commands.command()
    async def team_json(self, ctx):
        """
        This command outputs a json object that stores all the team and white shirt info.

        It is used to transport information from the bot to the LPD Station efficiently.
        """

        teams = deepcopy(self.bot.settings["teams"])
        json_out = []

        # Add the white shirts onto the teams list
        for rank in self.bot.settings["role_ladder"]:
            try:
                rank["is_white_shirt"]
            except KeyError:
                pass
            else:
                rank["has_unlock_all_button"] = True
                teams.append(rank)

        # Create the JSON from the team list
        for role_dict in teams:

            # Get the members
            role = self.bot.officer_manager.guild.get_role(role_dict["id"])
            try:
                members = self.get_role_members(role)
            except errors.GetRoleMembersError as error:
                await ctx.send(error)
                return

            # Add the JSON role object
            json_out.append(
                {
                    "id": role_dict["id"],
                    "name": self.filter_start_end(role.name, ["|", " ", "⠀", " "]),
                    "name_id": role_dict["name_id"],
                    "member_count": len(members),
                    "members": [self.get_vrc_name(m) for m in members],
                    "has_unlock_all_button": role_dict.get(
                        "has_unlock_all_button", False
                    ),
                    "is_white_shirt": role_dict.get("is_white_shirt", False),
                }
            )

        # Send the JSON file
        await send_long(ctx.channel, json.dumps(json_out), code_block=True)

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command()
    async def count_officers(self, ctx):
        """
        This command returns a chart including a total Officer count,
        and a count of Officers in each rank-role in the server.
        """
        # Call our function to get a list of roles
        settings = self.bot.settings
        role_ids = role_id_index(settings)

        # Build index of Officers, keeping only the highest role in the ladder
        all_officers = []
        guild = self.bot.officer_manager.guild
        for member in guild.members:
            for role in member.roles:
                if role.id in role_ids:
                    if member in all_officers:
                        del all_officers[-1]
                    all_officers.append(member)

        # Get a usable number of oficers, and create a dictionary for the count by role
        number_of_officers = len(all_officers)
        number_of_officers_with_each_role = {}

        # For every role in the role list, reverse sorted to preserve higher role:
        for entry in role_ids[::-1]:
            role = guild.get_role(entry)
            if (
                role is None
            ):  # If the role ID is invalid, let the user know what the role name should be, and that the ID in settings is invalid
                await ctx.channel.send(f"{ctx.message.author.mention} The role ID for {get_role_name_by_id(settings, entry)} has been corrupted in the bot configuration, therefore I cannot provide an accurate count. Please alert the Programming Team. Displayed below are the results of counting all other roles.")
            else:
                number_of_officers_with_each_role[
                    role
                ] = 0  # Create entry in the dictionary

        # This actually counts the officers per role
        for officer in all_officers:
            for role in number_of_officers_with_each_role:
                if role in officer.roles:
                    number_of_officers_with_each_role[role] += 1
                    break

        # Build the embed
        embed = discord.Embed(
            title="Number of all LPD Officers: " + str(number_of_officers),
            colour=discord.Colour.from_rgb(255, 255, 0),
        )

        pattern = re.compile(r"(LPD )?(\w+( \w+)*)")

        # Reverse the order of the dictionary, since we reversed the list earlier. This preserves the previous output of Cadet first, Chief last
        number_of_officers_with_each_role = dict(
            reversed(list(number_of_officers_with_each_role.items()))
        )

        # Make the embed look pretty with actual role names in server
        for role in number_of_officers_with_each_role:

            match = pattern.findall(role.name)
            if match:
                name = "".join(match[0][1]) + "s"
            else:
                name = role.name

            embed.add_field(
                name=name + ":", value=number_of_officers_with_each_role[role]
            )

        # Send the results
        await ctx.channel.send(embed=embed)


    @checks.is_lpd()
    @commands.command()
    async def join(self, ctx):
        officer_id = ctx.message.mentions[0].id
        vrc_name = self.bot.user_manager.get_vrc_by_discord(officer_id)
        join_link = await join_user(vrc_name)
        if join_link == "This user is in a Private World.":
            string = f"{ctx.message.mentions[0].mention} is in a Private World."
        else:
            string = f"Join {ctx.message.mentions[0].mention} {join_link}"
        await ctx.message.delete()
        await ctx.channel.send(string)
    
    @checks.is_lpd()
    @commands.command()
    async def invite(self, ctx):
        author_id = ctx.message.author.id
        vrc_name = self.bot.user_manager.get_vrc_by_discord(author_id)
        join_link = await join_user(vrc_name)
        if join_link == "This user is in a Private World.":
            string = "Could not generate an invite link for your location. It appears that you are in a Private World, or have your status set to Red or Orange."
        else:
            string = f"{ctx.message.mentions[0].mention} please join {ctx.message.author.mention} {join_link}"
        await ctx.message.delete()
        await ctx.channel.send(string)
        
        
        
    @checks.is_lpd()
    @commands.command()
    async def whereis(self, ctx):
        string = ''
        for target in ctx.message.mentions:
            officer = self.bot.officer_manager.get_officer(target.id)
            if officer.is_on_duty:
                
                location = officer.location
                
                string = f"{string}{target.mention} is in {location}\n"
            else:
                string = f"{string}{target.mention} is not on duty"
        await ctx.channel.send(string)
        
    
    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command()
    async def mug_stats(self, ctx):
        mugshots = await self.bot.officer_manager.send_db_request("select * from Mugshots order by officer_id", None)
        print(mugshots)
        
        statistics_dict = []
        
        all_officers = self.bot.officer_manager.all_officers
        
        for officer in all_officers:
            statistics_dict[str(officer.id)] = 0
            
        
        for mugshot in mugshot:
            arresting_officer_id = mugshot[0]
            world_name = mugshot[1]
            criminal_name = mugshot[2]
            officers_involved_string = mugshot[5]
            
            officers_involved_list = officers_involved_string.split(',')
            officers_involved = []
            
            for officer_id in officers_involved_list:
                officers_involved.append(int(officer_id))
            
            if arresting_officer_id not in officers_involved:
                officers_involved.append(arresting_officer_id)
                
                
            for officer_id in officers_involved:
                statistics_dict[str(officer_id)] += 1
                
                
                
        print(statistics_dict)