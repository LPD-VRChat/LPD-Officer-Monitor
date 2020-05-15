from discord.ext import commands
import texttable

from copy import deepcopy
import argparse
import re
from io import StringIO
import sys

from Classes.custom_arg_parse import ArgumentParser
import Classes.errors as errors

class Time(commands.Cog):
    """This stores all the time commands."""
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def seconds_to_string(onDutySeconds):

        #Calculate days, hours, minutes and seconds
        onDutyMinutes, onDutySeconds = divmod(onDutySeconds, 60)
        onDutyHours, onDutyMinutes = divmod(onDutyMinutes, 60)
        onDutyDays, onDutyHours = divmod(onDutyHours, 24)
        onDutyweeks, onDutyDays = divmod(onDutyDays, 7)

        # Move the time to the string
        on_duty_time_string = ""
        if onDutyweeks != 0:
            on_duty_time_string += "\nWeeks: "+str(onDutyweeks)
        if onDutyDays + onDutyweeks != 0:
            on_duty_time_string += "\nDays: "+str(onDutyDays)
        if onDutyHours + onDutyDays + onDutyweeks != 0:
            on_duty_time_string += "\nHours: "+str(onDutyHours)
        if onDutyMinutes + onDutyHours + onDutyDays + onDutyweeks != 0:
            on_duty_time_string += "\nMinutes: "+str(onDutyMinutes)
        on_duty_time_string += "\nSeconds: "+str(onDutySeconds)

        return on_duty_time_string

    @commands.command()
    async def user(self, ctx, *args):
        """
        This command gets the on duty time for an officer

        NAME
            =user - get on duty time and last active information
                    about a specific officer.

        SYNOPSIS
            =user [options] officer
        
        OPTIONS
            -d NUMBER,
            --days NUMBER
                specify the number of days to look back for 
                activity, this defaults to 28.

            -f DATE,
            --from-date DATE
                specify the date to look back at, if no --to-date
                is specified it will show all activity from the
                --from-date to right now.

            -t DATE,
            --to-date DATE
                specify the date to stop looking at, --from-date
                has to be specified with this option.
            
            -l,
            --list
                get a list of all patrols during the specified
                time period.
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

        # Find the officer ID
        p = re.compile(r"<@\![0-9]{18,20}>")
        match = p.match(parsed.officer)
        
        # Make sure someone is mentioned
        if not match:
            await ctx.send(ctx.author.mention+" Make sure to mention an officer.")
            return
        
        # Move the officer_id into a variable
        officer_id = int(match.group()[3:-1])
        print(f"officer_id: {officer_id}")
        
        # Make sure the person mentioned is an LPD officer
        officer = self.bot.officer_manager.get_officer(officer_id)
        if officer is None:
            await ctx.send(ctx.author.mention+" The person you mentioned is not being monitored, are you sure this person is an officer?")
            return
        
        
        # ====================
        # Parse extra options
        # ====================
        
        # Get the time and put it into an out string and also fill the days, from_date and to_date to use when
        # everything is printed out
        days = None
        from_date = None
        to_date = None

        # The user selected nothing and will get the automatic option
        if parsed.days == None and parsed.from_date == None and parsed.to_date == None:
            parsed.days = 28

        # The user selected a set amount of days
        if parsed.days:

            # Set the variable to store the days
            days = parsed.days

            # Set the out_string to store the first part of the message to the user
            out_string = "On duty time for "+officer.mention+" - last "+str(days)+ " days"

        # The user selected from or to dates
        elif parsed.from_date or parsed.to_date:

            # Make sure their is a from_date if their is a to date
            if parsed.to_date and not parsed.from_date:
                await ctx.send(ctx.author.mention+" If you want to use to-date you have to set a from-date.")
                return
            
            # Set the variables to store the from_date and to_date
            from_date = parsed.from_date
            to_date = parsed.to_date

            # Set the out_string to store the first part of the message to the user
            out_string = "On duty time for "+officer.mention+" - from: "+str(parsed.from_date)+"  to: "+str(parsed.to_date)
            out_string = out_string.replace("None", "Right now")


        # ====================
        # Output
        # ====================

        if not parsed.list:

            # Get the time in seconds
            if days: time_seconds = await officer.get_time_days(days)
            else: time_seconds = await officer.get_time_date(from_date, to_date)

            # Print the results out
            out_string += self.seconds_to_string(time_seconds)
            await ctx.send(out_string)

        else:
            
            # Get all the patrols
            if days: all_patrols = await officer.get_full_time_days(days)
            else: all_patrols = await officer.get_full_time_date(from_date, to_date)

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

class Other(commands.Cog):
    """This stores all the other commands that do not fit in one of the other categories."""
    def __init__(self, bot):
        self.bot = bot
        self.officer_manager = bot.officer_manager
    
