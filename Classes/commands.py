from discord.ext import commands

from .custom_arg_parse import ArgumentParser
import argparse
import re

class Time(commands.Cog):
    """This stores all the time commands."""
    def __init__(self, bot, officer_manager):
        self.bot = bot
        self.officer_manager = officer_manager

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
        NAME
            ?user - get on duty time and last active information
                    about a specific officer.

        SYNOPSIS
            ?user [options] officer
        
        OPTIONS
            --days=NUMBER
                specify the number of days to look back for activity,
                this defaults to 28.

            --from-date=DATE
                specify the date to look back at, if no --to-date
                is specified it will show all activity from the
                --from-date to right now.

            --to-date=DATE
                specify the date to stop looking at, --from-date
                has to be specified with this option.
        """

        parser = ArgumentParser(description="Argparse user command")
        parser.add_argument('officer')
        parser.add_argument("-d", "--days", type=int)
        parser.add_argument("-f", "--from-date")
        parser.add_argument("-t", "--to-date")

        try: parsed = parser.parse_args(args)
        except argparse.ArgumentError:
            await ctx.send(ctx.author.mention+" This is an error in your command syntax.")
            return
        except argparse.ArgumentTypeError:
            await ctx.send(ctx.author.mention+" One of your arguments is the wrong type. For example putting in text where a number is expected.")
            return

        p = re.compile(r"<@[0-9]{18,20}>")
        match = p.match(parsed.officer)
        if match:
            officer_id = match.group()[2:-1]
            print(officer_id)
        else:
            print("No officer found")
            
        officer = self.officer_manager.get_officer(officer_id)
        

        await ctx.send(str(parsed), officer)