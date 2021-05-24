# Standard
from Classes.Officer import Officer
import csv
import sys
from copy import deepcopy
import argparse
import re
from io import StringIO, BytesIO
from datetime import datetime, timedelta
import time
import math
import traceback
import json
import asyncio
from typing import Any, Dict, List, Set, Tuple, Union
import fuzzywuzzy.process

# Community
import discord
from discord.ext import commands
import texttable
import arrow

# Mine
from Classes.extra_functions import (
    send_long,
    handle_error,
    get_rank_id,
    has_role,
    send_str_as_file,
    clean_shutdown,
)
from Classes.custom_arg_parse import ArgumentParser
from Classes.menus import Confirm
import Classes.errors as errors
import Classes.checks as checks
from Classes.extra_functions import role_id_index, get_role_name_by_id


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
        p = re.compile(r"<@!{0,1}([0-9]+?)>")
        match = p.match(officer_string)
        if match:
            return int(match.group(1))

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
                to_datetime = datetime.utcnow()

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
            await ctx.send("Make sure to mention an officer.")
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
            def draw_table(table):
                return "```\n" + table.draw() + "\n```"

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
            datetime.utcnow() - timedelta(days=28), datetime.utcnow(), limit=None
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
            active_days_ago = (datetime.utcnow() - last_activity["time"]).days
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

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command()
    async def time_to_1_csv(self, ctx):
        """
        This command converts the time to the LPD Officer Monitor 1.0s csv format and
        sends it throguh discord.
        """
        await ctx.send("Please give me some time, this may take several minutes.")

        # This opens a virtual file in memory that can be written to by the CSV module
        with StringIO() as virtual_bot_1_time_file:
            csv_writer = csv.writer(virtual_bot_1_time_file)
            for id, officer in self.bot.officer_manager.all_officers.items():

                # Get the last active time for the officer
                last_active_time_datetime = (
                    await officer.get_last_activity(
                        self.bot.settings["monitored_channels"]
                    )
                )["time"]
                last_active_time = (
                    last_active_time_datetime - datetime(1970, 1, 1)
                ).total_seconds()
                if last_active_time is None:
                    last_active_time = 0

                # Get the patrol time
                to_time = datetime.utcnow()
                from_time = to_time - timedelta(28)
                patrol_time = await officer.get_time(from_time, to_time)

                # Add both to the CSV file
                csv_writer.writerow([officer.id, last_active_time, patrol_time])

            await send_str_as_file(
                channel=ctx.channel,
                file_data=virtual_bot_1_time_file.getvalue(),
                filename="LPD_database.csv",
                msg_content=f"{ctx.author.mention} Here is the time file compatable with LPD Officer Monitor 1.0:",
            )


class Inactivity(commands.Cog):
    """Here are all the commands relating to Leaves of Absence and Inactivity"""

    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.blurple()

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command()
    async def mark_inactive(self, ctx):
        """
        This command lists inactive officers, and prompts the user to mark them with the LPD_inactive role.
        Use the `-i` flag to mark officers inactive individually.
        """

        # Get all fields from LeaveTimes
        loa_entries = await self.bot.officer_manager.get_loa()

        # If the entry is still good, add the officer to our exclusion list. Otherwise, delete the entry if expired.
        loa_officer_ids = {entry[0] for entry in loa_entries}

        # For everyone in the server where their role is in the role ladder,
        # get their last activity times, or if no last activity time, use
        # the time we started monitoring them. Exclude those we have already
        # determined have a valid Leave of Absence

        # Get a date range for our LOAs, and make some dictionaries to work in
        min_activity = self.bot.settings["min_activity_minutes"]
        max_inactive_days = self.bot.settings["max_inactive_days"]
        max_inactive_msg_days = self.bot.settings["max_inactive_msg_days"]
        oldest_valid = datetime.utcnow() - timedelta(days=max_inactive_days)
        oldest_valid_msg = datetime.utcnow() - timedelta(days=max_inactive_msg_days)

        # Find officers with too little patrol time and no LOA
        officer_activity = await self.bot.officer_manager.get_most_active_officers(
            oldest_valid, datetime.utcnow(), include_no_activity=True
        )
        not_enough_patrol: List[Officer] = []
        for officer_id, active_seconds in officer_activity:
            active_seconds = active_seconds or 0
            if officer_id not in loa_officer_ids and active_seconds < min_activity * 60:
                officer = self.bot.officer_manager.get_officer(officer_id)
                not_enough_patrol.append(officer)

        # Get their last activity in chat and make sure it's recent enough
        monitored = self.bot.settings["monitored_channels"]
        # Create the tasks set
        tasks: Set[asyncio.Task[Union[Dict[str, Any], None]]] = set()
        for officer in not_enough_patrol:
            new_coroutine = officer.get_last_activity(monitored)
            new_task = asyncio.create_task(new_coroutine)
            new_task.officer = officer
            tasks.add(new_task)
        done, _ = await asyncio.wait(tasks)
        # Make sure the officers have been active enough in monitored chats
        inactive_officers = []
        chat_activity_skipped = []
        for finished_task in done:
            activity_dict = finished_task.result()
            officer = finished_task.officer
            if activity_dict["time"] < oldest_valid_msg:
                inactive_officers.append(officer)
            else:
                chat_activity_skipped.append(officer)

        if len(inactive_officers) == 0:
            await ctx.channel.send(
                "There are no inactive officers found without a leave of absence."
            )
            return

        role = self.bot.officer_manager.guild.get_role(
            self.bot.settings["inactive_role"]
        )

        if "-i" in ctx.message.content:
            for officer in inactive_officers:
                confirm = await Confirm(
                    f"Do you want to mark {officer.mention} as inactive?"
                ).prompt(ctx)
                if confirm:
                    await officer.member.add_roles(role)
                    await ctx.channel.send(
                        f"{officer.mention} has been marked as inactive."
                    )
                else:
                    await ctx.channel.send(
                        f"{officer.mention} will have their inactivity reevaluated at a later date."
                    )
        else:
            output_string = ""
            for officer in inactive_officers:
                output_string = f"{officer.mention}\n{output_string}"
            await send_long(ctx.channel, output_string, mention=False)
            confirm = await Confirm(
                f"Do you want to mark the officers above as inactive?"
            ).prompt(ctx)
            if confirm:
                for officer in inactive_officers:
                    await officer.member.add_roles(role)
                await ctx.channel.send(
                    f"All officers above have been marked as inactive."
                )
            else:
                await ctx.channel.send("Cancelled.")

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command()
    async def show_loa(self, ctx):
        """
        This command displays all Leave of Absence requests currently on file.
        """
        loa_entries = await self.bot.officer_manager.get_loa()

        if len(loa_entries) == 0:
            string = "There are no Leaves of Absence on file at this time."

        else:
            for entry in loa_entries:
                officer = self.bot.get_user(entry[0])
                string = f"There are currently Leaves of Absence on file for the following Officers:"
                string = f"{string}\n{officer.mention} from {entry[1]} to {entry[2]} for reason: {entry[3]}"
                if len(string) > 1000:
                    await ctx.channel.send(string)
                    string = ""

        await ctx.channel.send(string)


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

    @commands.command(usage='[-s] "my username"')
    @checks.is_lpd()
    @checks.is_general_bot_channel()
    async def link(self, ctx, *args):
        r"""
        This command is used to tell the bot your VRChat name.

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

        if not args:
            await ctx.channel.send("Please specify your VRChat name.")
            return

        # Check if -s is specified
        if args[0] == "-s":
            if len(args) == 1:
                await ctx.channel.send("Please specify your VRChat name.")
                return
            skip_formatting = True
        else:
            skip_formatting = False

        # if use spaces without quotes, won't add space if only one
        vrchat_name = " ".join(args[int(skip_formatting) :])

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

        # Format the VRChat name if that was asked for
        if skip_formatting:
            vrchat_formated_name = vrchat_name
        else:
            vrchat_formated_name = self.bot.user_manager.vrc_name_format(vrchat_name)

        # Confirm the VRC name
        confirm = await Confirm(
            f"Are you sure `{vrchat_formated_name}` is your full VRChat name?\n**You will be held responsible of the actions of the VRChat user with this name.**"
        ).prompt(ctx)
        if confirm:
            await self.bot.user_manager.add_user(
                ctx.author.id, vrchat_name, skip_formatting
            )
            await ctx.send(
                f"Your VRChat name has been set to `{vrchat_formated_name}`\nIf you want to unlink it you can use the command =unlink"
            )
        else:
            await ctx.send(
                "Your account linking has been cancelled, if you did not intend to cancel the linking you can use the command =link again."
            )

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


class Moderation(commands.Cog):
    """Here are all commands that relate to moderation in general."""

    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.green()

    @checks.is_chat_moderator()
    @commands.command()
    # Put a user in detention
    async def detain(self, ctx):
        """
        This command places a user in detention by assigning the Detention and Detention Waiting Area roles.
        Chat moderators may use this to effectively temp ban a user without having the ban permission.
        This command should only be used when the severity of violation is extreme. Use strike when possible.
        """
        detainees = ctx.message.mentions
        detention_role = self.bot.officer_manager.guild.get_role(
            self.bot.settings["detention_role"]
        )
        detention_waiting_area_role = self.bot.officer_manager.guild.get_role(
            self.bot.settings["detention_waiting_area_role"]
        )
        detainee_mentions = ""
        undet_string = ""

        for user in detainees:

            # If the user is an officer and holds a non-detainable rank: skip them
            officer = self.bot.officer_manager.get_officer(user.id)
            if officer and not officer.is_detainable:
                undet_string = f"{undet_string}{user.mention}"
                continue

            user_role_ids = ""
            for role in user.roles:
                if role.name == "@everyone":
                    continue
                user_role_ids = f"{role.id},{user_role_ids}"
                await user.remove_roles(role)
            await user.add_roles(detention_role)
            await user.add_roles(detention_waiting_area_role)
            detainee_mentions = f"{detainee_mentions}{user.mention}"
            await self.bot.sql.request(
                f"REPLACE INTO Detainees (member_id, roles, date) VALUES ({user.id}, '{user_role_ids}', '{datetime.utcnow()}')"
            )

        if len(detainee_mentions) > 0:
            await ctx.channel.send(
                f'{self.bot.officer_manager.guild.get_role(self.bot.settings["moderator_role"]).mention} Moved {detainee_mentions} to detention.'
            )
        if len(undet_string) > 0:
            await ctx.channel.send(
                f"Sorry, you can't detain {undet_string}. Only Senior Officers and below may be detained."
            )

    @checks.is_moderator()
    @commands.command()
    # Remove a user from detention
    async def restore(self, ctx):
        """
        This command removes a non-LPD user from detention by removing the Detention and Detention Waiting Area roles.
        Use of this command is restricted to Moderators and above.
        """
        detainees = ctx.message.mentions
        detention_role = self.bot.officer_manager.guild.get_role(
            self.bot.settings["detention_role"]
        )
        detention_waiting_area_role = self.bot.officer_manager.guild.get_role(
            self.bot.settings["detention_waiting_area_role"]
        )
        string = "Removing"
        send_string = 0

        for user in detainees:
            remove_from_db = 0
            for role in user.roles:
                if role.id == detention_role.id:
                    send_string = 1
                    remove_from_db = 1
                    await user.remove_roles(detention_role)
                if role.id == detention_waiting_area_role.id:
                    send_string = 1
                    remove_from_db = 1
                    await user.remove_roles(detention_waiting_area_role)
            if remove_from_db == 1:
                user_role_list = list(
                    await self.bot.sql.request(
                        f"SELECT roles FROM Detainees WHERE member_id = {user.id}"
                    )
                )
                for role_id in user_role_list[0][0].split(","):
                    if role_id == "":
                        continue
                    await user.add_roles(
                        self.bot.officer_manager.guild.get_role(int(role_id))
                    )
                await self.bot.sql.request(
                    f"DELETE FROM Detainees WHERE member_id = {user.id}"
                )
                remove_from_db = 0
                string = f"{string} {user.mention}"

        string = f"{string} from detention."
        if send_string == 1:
            await ctx.channel.send(string, delete_after=10)
        else:
            await ctx.channel.send(
                "Please mention valid users you wish to release from detention.",
                delete_after=10,
            )

    @checks.is_chat_moderator()
    @commands.command()
    async def strike(self, ctx):
        """
        This command issues a warning strike to the user(s) mentioned.
        """

        detention_role = self.bot.officer_manager.guild.get_role(
            self.bot.settings["detention_role"]
        )
        detention_waiting_area_role = self.bot.officer_manager.guild.get_role(
            self.bot.settings["detention_waiting_area_role"]
        )

        users_detained = ""
        strikee_mentions = ""
        undet_string = ""
        for user in ctx.message.mentions:

            # If the user is an officer and holds a non-detainable rank: skip them
            officer = self.bot.officer_manager.get_officer(user.id)
            if officer and not officer.is_detainable:
                undet_string = f"{undet_string}{user.mention}"
                continue

            await self.bot.sql.request(
                f"INSERT INTO UserStrikes (member_id, reason, date) VALUES ({user.id}, '{ctx.message.content}', '{datetime.utcnow()}')"
            )
            strikee_mentions = f"{strikee_mentions}{user.mention}"
            old_strikes = list(
                await self.bot.sql.request(
                    f"SELECT date FROM UserStrikes WHERE member_id = {user.id}"
                )
            )
            for date in old_strikes:
                if date[0] <= datetime.utcnow() - timedelta(days=14):
                    old_strikes.remove(date)
                    await self.bot.sql.request(
                        f"DELETE FROM UserStrikes WHERE member_id = {user.id} and date = '{date[0]}'"
                    )
                    continue
            if len(old_strikes) >= 3:
                users_detained = f"{users_detained}{user.mention}"
                # user_role_ids = ""
                # for role in user.roles:
                #     if role.name == '@everyone': continue
                #     user_role_ids = f"{role.id},{user_role_ids}"
                #     await user.remove_roles(role)
                # await user.add_roles(detention_role)
                # await user.add_roles(detention_waiting_area_role)
                # await self.bot.sql.request(f"REPLACE INTO Detainees (member_id, roles, date) VALUES ({user.id}, '{user_role_ids}', '{datetime.utcnow()}')")

        if len(strikee_mentions) > 0:
            await ctx.channel.send(
                f"{strikee_mentions} received a strike against their record.",
                delete_after=10,
            )
        if len(undet_string) > 0:
            await ctx.channel.send(
                f"Sorry, {undet_string} cannot be given a strike. Only Senior Officers and below can be given a strike."
            )
        if len(users_detained) > 0:
            await ctx.channel.send(
                f'{self.bot.officer_manager.guild.get_role(self.bot.settings["moderator_role"]).mention} {users_detained} have received 3 strikes in the last two weeks.'
            )


class Other(commands.Cog):
    """Here are all the one off commands that I have created and are not apart of any group."""

    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.dark_magenta()
        self.get_vrc_name = (
            lambda x: self.bot.user_manager.get_vrc_by_discord(x.id) or x.display_name
        )

    @staticmethod
    def remove_name_decoration(name: str) -> str:
        """
        Remove the discord special characters at the start and end of the string
        """
        return name.strip("| ⠀ ")

    def get_role_by_name(self, role_name: str) -> discord.Role:
        """
        Return a discord role if found, else raise `errors.GetRoleMembersError`
        """
        role_names = []

        # Get the role
        for role in self.bot.officer_manager.guild.roles:
            undecorated_name = self.remove_name_decoration(role.name)
            role_names.append(undecorated_name)
            if (
                undecorated_name.lower() == role_name.lower()
            ):  # non case sensitive comparaison
                return role

        msg = f"The role `{role_name}` was not found.\nDid you mean :"
        cutoff_score = 75
        suggestions: List[Tuple[str, int]] = []

        # usually you get something on the first run, sometimes if you write really badly you won't get anything
        # lower the score to get more suggestions
        while len(suggestions) < 1 and len(role_name) > 1 and cutoff_score > 0:
            suggestions = fuzzywuzzy.process.extractBests(
                role_name, role_names, score_cutoff=cutoff_score
            )
            # if only one suggestion, give result imediatly instead of suggest and having to type cmd again
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

    def get_role_members(self, role: discord.Role) -> list:
        # Make sure that people have the role
        if not role.members:
            raise errors.GetRoleMembersError(message=f"`{role.name}` is empty.")

        # Sort the members
        return sorted(role.members, key=lambda m: self.get_vrc_name(m).lower())

    @checks.is_team_bot_channel()
    @commands.check_any(
        checks.is_white_shirt(), checks.is_dev_team(), checks.is_team_lead()
    )
    @commands.command()
    async def rtv(self, ctx, role_name):
        """
        This command takes in a name of a role and outputs the VRC names of the people in it.

        This command ignores the decoration on the role if it has any and it also requires
        """

        try:
            discord_role = self.get_role_by_name(role_name)
            members = self.get_role_members(discord_role)
        except errors.GetRoleMembersError as error:
            await ctx.send(error)
            return

        members_str = "\n".join(self.get_vrc_name(x) for x in members)

        # Send everyone
        await ctx.send(
            f"Here is everyone in the role `{self.remove_name_decoration(discord_role.name)}`:"
        )
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
                    "name": self.remove_name_decoration(role.name),
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
                await ctx.channel.send(
                    f"{ctx.message.author.mention} The role ID for {get_role_name_by_id(settings, entry)} has been corrupted in the bot configuration, therefore I cannot provide an accurate count. Please alert the Programming Team. Displayed below are the results of counting all other roles."
                )
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

            """
            elif role.name == "||  ⠀⠀⠀⠀⠀⠀Cadet ⠀⠀⠀⠀⠀⠀  ||":
                name = 'Cadets'
            Leaving this here for future use if needed.
            """

            embed.add_field(
                name=name + ":", value=number_of_officers_with_each_role[role]
            )

        # Send the results
        await ctx.channel.send(embed=embed)

    @checks.is_team_bot_channel()
    @checks.is_programming_team()
    @commands.command()
    async def shutdown(self, ctx):
        """This command shuts down the bot cleanly."""

        await ctx.channel.send("Shutting down the bot now!")
        whostr = f"{ctx.channel.name} by {ctx.author.display_name}"
        await clean_shutdown(self.bot, ctx.channel.name, ctx.author.display_name)
