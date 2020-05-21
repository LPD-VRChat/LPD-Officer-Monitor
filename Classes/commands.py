# Standard
from copy import deepcopy
import argparse
import re
from io import StringIO
import sys
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import time
import math

# Community
import discord
from discord.ext import commands
import texttable
import arrow

# Mine
from Classes.custom_arg_parse import ArgumentParser
import Classes.errors as errors
from Classes.extra_functions import send_long


class Time(commands.Cog):
    """Here are all the commands relating to managing the time of officers."""
    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.blue()


    # Time functions

    @staticmethod
    def seconds_to_string(seconds, multi_line=True):

        # Calculate days, hours, minutes and seconds
        onDutyMinutes, onDutySeconds = divmod(seconds, 60)
        onDutyHours, onDutyMinutes = divmod(onDutyMinutes, 60)
        onDutyDays, onDutyHours = divmod(onDutyHours, 24)
        
        onDutyweeks, onDutyDaysWithWeeks = divmod(onDutyDays, 7)

        # Move the time to the string
        if multi_line:
            on_duty_time_string = ""
            if onDutyweeks != 0:
                on_duty_time_string += f"\nWeeks: {onDutyweeks}"
            if onDutyDaysWithWeeks + onDutyweeks != 0:
                on_duty_time_string += f"\nDays: {onDutyDaysWithWeeks}"
            if onDutyHours + onDutyDaysWithWeeks + onDutyweeks != 0:
                on_duty_time_string += f"\nHours: {onDutyHours}"
            if onDutyMinutes + onDutyHours + onDutyDaysWithWeeks + onDutyweeks != 0:
                on_duty_time_string += f"\nMinutes: {onDutyMinutes}"
            on_duty_time_string += f"\nSeconds: {onDutySeconds}"

            return on_duty_time_string
        else:
            return f"{onDutyDays}:{onDutyHours}:{onDutyMinutes}:{onDutySeconds}"

    def get_officer_id(self, officer_string):
    
        # Check for an @ mention
        p = re.compile(r"<@\![0-9]+>")
        match = p.match(officer_string)
        if match: return int(match.group()[3:-1])
        
        # Check for an ID
        p = re.compile(r"[0-9]+")
        match = p.match(officer_string)
        if match: return int(match.group())

        # Nothing was found
        return None

    def create_last_active_embed(self, officer, time_results):

        if not time_results: embed = discord.Embed(description="No activity recorded")
        else: embed = discord.Embed(description="Latest activity")

        # Set the author of the embed
        embed.set_author(
            name=officer.display_name,
            icon_url=officer.member.avatar_url
        )

        # Return the embed if their are no results to add
        if not time_results: return embed

        # Order the time_results:
        time_results = sorted(time_results, key=lambda x: time.mktime(x["time"].timetuple()), reverse=True)

        # Add the channels
        for result in time_results:
            if result['channel_id'] == None:
                embed.add_field(
                    name=arrow.Arrow.fromdatetime(result["time"]).humanize(),
                    value=result["other_activity"]
                )
            else:
                url = f"https://discordapp.com/channels/{self.bot.officer_manager.guild.id}/{result['channel_id']}/{result['message_id']}"
                embed.add_field(
                    name=arrow.Arrow.fromdatetime(result["time"]).humanize(),
                    value=f"[#{self.bot.get_channel(result['channel_id']).name}]({url})"
                )
        
        return embed

    @staticmethod
    def parse_date(date_string):
        date = date_string.split("/")

        # Make sure the length is correct
        if len(date) != 3:
            raise ValueError("Their is an error in the date you put in, make sure to split the date with a slash. Example: 30/2/2020")
        
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

        # The user selected nothing and will get the automatic option
        if parsed.days == None and parsed.from_date == None and parsed.to_date == None:
            parsed.days = 28

        # The user selected a set amount of days
        if parsed.days:

            # Create the datetime objects from the number of second since epoc
            from_datetime = datetime.fromtimestamp(math.floor(time.time() - parsed.days * 86400))
            to_datetime = datetime.fromtimestamp(math.floor(time.time()))

            time_string = f"for the last {parsed.days} days"

        # The user selected from or to dates
        elif parsed.from_date or parsed.to_date:

            if from_datetime == None and to_datetime != None:
                # The user wants the from_time to be the current time
                from_datetime = datetime.now(timezone.utc)
                to_datetime = self.parse_date(parsed.to_date)

            elif from_datetime != None and to_datetime == None:
                # The user wants the to_datetime to be 28 days from from_datetime
                from_datetime = self.parse_date(parsed.from_date)
                to_datetime = from_datetime + timedelta(days=28)

            else:
                # Both are here, they can just be parsed
                from_datetime = self.parse_date(parsed.from_date)
                to_datetime = self.parse_date(parsed.to_date)
            
            # Set the out_string to store the first part of the message to the user
            time_string = f'from: {from_datetime.strftime("%d/%m/%Y")}  to: {to_datetime.strftime("%d/%m/%Y")}'
    
        return (time_string, from_datetime, to_datetime)


    # Commands

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
        parser.add_argument('officer')
        parser.add_argument("-d", "--days", type=int)
        parser.add_argument("-f", "--from-date")
        parser.add_argument("-t", "--to-date")
        parser.add_argument("-l", "--list", action="store_true")

        # Parse command and check errors
        try: parsed = parser.parse_args(args)
        except argparse.ArgumentError as error:
            await ctx.send(ctx.author.mention+" "+str(error))
            return
        except argparse.ArgumentTypeError as error:
            await ctx.send(ctx.author.mention+" "+str(error))
            return
        except errors.ArgumentParsingError as error:
            await ctx.send(ctx.author.mention+" "+str(error))
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
            await ctx.send("The person you mentioned is not being monitored, are you sure this person is an officer?")
            return
        

        # ====================
        # Get the datetime
        # ====================

        try: time_text, from_datetime, to_datetime = self.parse_days_date_input(parsed)
        except ValueError as error:
            ctx.send(error)
            return
        out_string = f"On duty time for {officer.mention} - {time_text}"


        # ====================
        # Output
        # ====================

        if not parsed.list:

            # Get the time in seconds
            time_seconds = await officer._get_time_datetime(from_datetime, to_datetime)

            # Print the results out
            out_string += self.seconds_to_string(time_seconds)
            await ctx.send(out_string)

        else:
            
            # Get all the patrols
            all_patrols = officer._get_full_time_datetime(from_datetime, to_datetime)

            # Send the header
            await ctx.send(out_string)
            out_string = ""

            # Set up the header of the table
            table = texttable.Texttable()
            table.header(["From      ", "To        ", "Seconds  "])

            # This is a lambda to add the discord code block on the table to keep it monospace
            draw_table = lambda table: "```\n"+table.draw()+"\n```"
            
            # Loop through all the patrols to add them to a string and send them
            for patrol in all_patrols:

                # Store the old table in case the new one gets too long
                old_table = draw_table(table)

                # This is the timeformat the tables will show
                time_format = "%d/%m/%Y"

                # Add the next row
                table.add_row([
                    str(patrol[0].strftime(time_format)),
                    str(patrol[1].strftime(time_format)),
                    str(patrol[2])
                ])

                # This executes if the table is too long to be sent in one discord message
                if len(draw_table(table)) >= 2000:

                    # Send the old table because the new one is too long to send
                    await ctx.send(old_table)
                    
                    # Create a new table and add the current row to it
                    table = texttable.Texttable()
                    table.add_row([
                        str(patrol[0].strftime(time_format)),
                        str(patrol[1].strftime(time_format)),
                        str(patrol[2])
                    ])
            
            # Send the table if it is not empty
            if len(table.draw()) > 0: await ctx.send(draw_table(table))

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
            await ctx.send("The person you mentioned is not being monitored, are you sure this person is an officer?")
            return

        # Get the time
        result = await officer.get_all_activity(ctx.bot.officer_manager.all_monitored_channels)

        # Send the embed
        await ctx.send(embed=self.create_last_active_embed(officer, result))

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
        try: parsed = parser.parse_args(args)
        except argparse.ArgumentError as error:
            await ctx.send(ctx.author.mention+" "+str(error))
            return None
        except argparse.ArgumentTypeError as error:
            await ctx.send(ctx.author.mention+" "+str(error))
            return
        except errors.ArgumentParsingError as error:
            await ctx.send(ctx.author.mention+" "+str(error))
            return

        # Parse the day input
        try: time_text, from_datetime, to_datetime = self.parse_days_date_input(parsed)
        except ValueError as error:
            ctx.send(error)
            return

        # Get the time for all the officers
        all_times = await self.bot.officer_manager.get_most_active_officers(parsed.how_many_officers, from_datetime, to_datetime)
        
        # Format the output and send it
        output_list = []
        output_list.append(f"Top on duty times - {time_text}:")
        output_list.append("Officer | On duty time")
        for officer_result in all_times:
            officer = self.bot.officer_manager.get_officer(officer_result[0])
            time_string = self.seconds_to_string(officer_result[1], multi_line=False)
            
            output_list.append(f"{officer.mention} | {time_string}")

        await send_long(ctx.channel, "\n".join(output_list))
