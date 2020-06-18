# Standard
import sys
from copy import deepcopy
import argparse
import re
from io import StringIO, BytesIO
from datetime import datetime, timedelta, timezone
import time
import math
import traceback

# Community
import discord
from discord.ext import commands
import texttable
import arrow

# Mine
from Classes.extra_functions import send_long, handle_error, get_rank_id
from Classes.custom_arg_parse import ArgumentParser
from Classes.menus import Confirm
import Classes.errors as errors
import Classes.checks as checks


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
        time_string = None

        # The user selected nothing and will get the automatic option
        if parsed.days == None and parsed.from_date == None and parsed.to_date == None:
            parsed.days = 28

        # The user selected a set amount of days
        if parsed.days != None:

            # Create the datetime objects from the number of second since epoc
            from_datetime = datetime.fromtimestamp(math.floor(time.time() - parsed.days * 86400))
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
        parser.add_argument('officer')
        parser.add_argument("-d", "--days", type=int)
        parser.add_argument("-f", "--from-date")
        parser.add_argument("-t", "--to-date")
        parser.add_argument("-l", "--list", action="store_true")

        # Parse command and check errors
        cmd = f"self.bot.command_prefix"
        try: parsed = parser.parse_args("=patrol_time", args)
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
            time_seconds = await officer.get_time(from_datetime, to_datetime)

            # Print the results out
            out_string += self.seconds_to_string(time_seconds)
            await ctx.send(out_string)

        else:
            
            # Get all the patrols
            all_patrols = await officer.get_full_time(from_datetime, to_datetime)

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
            await ctx.send("The person you mentioned is not being monitored, are you sure this person is an officer?")
            return

        # Get the time
        result = await officer.get_all_activity(ctx.bot.officer_manager.all_monitored_channels)

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
        try: parsed = parser.parse_args("=top", args)
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
        all_times = await self.bot.officer_manager.get_most_active_officers(
            from_datetime,
            to_datetime,
            limit=parsed.how_many_officers
        )
        
        # Format the output and send it
        output_list = []
        output_list.append(f"Top on duty times - {time_text}:")
        output_list.append("Officer | On duty time")
        for officer_result in all_times:
            officer = self.bot.officer_manager.get_officer(officer_result[0])
            time_string = self.seconds_to_string(officer_result[1], multi_line=False)
            
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
        try: required_hours = int(required_hours)
        except ValueError:
            await ctx.send("required_hours needs to be a number.")
            return

        # Get everyone that has been active enough
        all_times = await self.bot.officer_manager.get_most_active_officers(
            datetime.now(timezone.utc) - timedelta(days=28),
            datetime.now(timezone.utc),
            limit = None
        )

        # Filter list for only recruits that have been active enough
        all_officers_for_promotion = []
        for row in all_times:
            officer = self.bot.officer_manager.get_officer(row[0])
            
            recruit_role_id = self.bot.officer_manager.get_settings_role("recruit")["id"]
            if officer and recruit_role_id in (x.id for x in officer.member.roles) and row[1] >= required_hours*3600:
                all_officers_for_promotion.append(officer)
        
        # Format the output and send it
        if len(all_officers_for_promotion) == 0:
            await ctx.send(f"Their are no recruits that have been active for {required_hours} hours in the last 28 days.")
        else:
            out_str = "\n".join((
                f"Recruits that have been active for {required_hours} hours in the last 28 days:",
                "\n".join(f"@{x.discord_name}" for x in all_officers_for_promotion)
            ))
            await send_long(ctx.channel, out_str)

    @checks.is_admin_bot_channel()
    @checks.is_admin()
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
        result = await Confirm("Are you sure you want to promote all the recruits you mentioned to officer?").prompt(ctx)
        if result != True:
            await ctx.send("The promotion has been cancelled.")
            return

        # Set up some global variables
        guild = self.bot.officer_manager.guild
        recruit_role = guild.get_role(self.bot.officer_manager.get_settings_role("recruit")["id"])
        officer_role = guild.get_role(self.bot.officer_manager.get_settings_role("officer")["id"])

        # Promote everyone
        try:

            await ctx.send("I am now promoting everyone, please give me a few minutes.")

            for member in ctx.message.mentions:
                # Make sure the officer is a recruit
                if recruit_role.id in (x.id for x in member.roles):
                    await member.add_roles(officer_role)
                    await member.remove_roles(recruit_role)

            await ctx.send("Everyone has been promted to officer successfully.")

        except Exception as error:
            await ctx.send("**Not everyone was promoted to officer successfully**. Please go through and manually change the roles of members that did not get promoted. Please also contact Hroi so that he can fix the bot before next officer promotions happen.")
            await handle_error(ctx.bot, error, traceback.format_exc())

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
        if vrchat_name: await ctx.send(f'You have a VRChat account linked with the name `{vrchat_name}`, if you want to unlink it use the command =unlink or if you want to update your VRChat name use the command =link new_vrchat_name.')
        else: await ctx.send("You do not have a VRChat account linked, to connect your VRChat account do =link your_vrchat_name.")

    @commands.command()
    @checks.is_lpd()
    @checks.is_general_bot_channel()
    async def link(self, ctx, vrchat_name):
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

        # Make sure the name does not contain the seperation character
        if self.bot.settings["name_separator"] in vrchat_name:
            hroi = self.bot.get_guild(self.bot.settings["Server_ID"]).get_member(378666988412731404)
            await ctx.send(f'The name you put in contains a character that cannot be used "{self.bot.settings["name_separator"]}" please change your name or contact {hroi.mention} so that he can change the illegal character.')
            return

        # If the officer already has a registered account
        previous_vrchat_name = self.bot.user_manager.get_vrc_by_discord(ctx.author.id)
        if previous_vrchat_name:
            confirm = await Confirm(f'You already have a VRChat account registered witch is `{previous_vrchat_name}`, do you want to replace that account?').prompt(ctx)
            if not confirm:
                await ctx.send("Your account linking has been cancelled, if you did not intend to cancel the linking you can use the command =link again.")
                return

        # Confirm the VRC name
        confirm = await Confirm(f'Are you sure `{vrchat_name}` is your full VRChat name?\n**You will be held responsible of the actions of the VRChat user with this name.**').prompt(ctx)
        if confirm:
            await self.bot.user_manager.add_user(ctx.author.id, vrchat_name)
            await ctx.send(f'Your VRChat name has been set to `{vrchat_name}`\nIf you want to unlink it you can use the command =unlink')
        else:
            await ctx.send("Your account linking has been cancelled, if you did not intend to cancel the linking you can use the command =link again.")
    
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

        confirm = await Confirm(f'Your VRChat name is currently set to `{vrchat_name}`. Do you want to unlink that?').prompt(ctx)
        if confirm:
            await self.bot.user_manager.remove_user(ctx.author.id)
            await ctx.send('Your VRChat name has been successfully unlinked, if you want to link another account you can do that with =link.')
        else:
            await ctx.send(f'Your VRChat accout has not been unlinked and is still `{vrchat_name}`')
    
    @commands.command()
    @checks.is_white_shirt()
    @checks.is_admin_bot_channel()
    async def lvn(self, ctx):
        """
        This command is used to get the VRChat names of the people that are LPD Officers.
        
        The output from this command is only intended to be read by computers and is not
        easy to read for humans.
        """
        sep_char = self.bot.settings["name_separator"]
        vrc_names = [x[1] for x in self.bot.user_manager.all_users]
        
        output_text = f"{sep_char.join(vrc_names)}"
        if len(output_text) == 0: await ctx.send("There are no registered users.")
        elif len(output_text) < 2000: await ctx.send(output_text)
        else:
            with StringIO(output_text) as error_file_sio:
                with BytesIO(error_file_sio.read().encode('utf8')) as error_file:
                    await ctx.send("The output is too big to fit in a discord message so it is insted in a file.", file=discord.File(error_file, filename="all_vrc_names.txt"))

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
        result = await Confirm("Are you sure you want to add all the members you mentioned to the LPD?").prompt(ctx)
        if not result: await ctx.send("Officer adding canceled.")
        else:
            # Store the bots messages
            bot_messages = []

            # Update the roles for all the members
            bot_messages.append(await ctx.send("Please give me one moment while I update everyone's roles."))
            for member in ctx.message.mentions:
                # Make sure the member is not an officer already
                if self.bot.officer_manager.is_officer(member):
                    bot_messages.append(await ctx.send(f"{member.mention} is already an officer and has been skipped."))
                    continue

                # Get the roles to be updated
                lpd_role = self.bot.officer_manager.guild.get_role(self.bot.settings["lpd_role"])
                recruit_role = self.bot.officer_manager.guild.get_role(get_rank_id(self.bot.settings, "cadet"))
                civilian_role = self.bot.officer_manager.guild.get_role(self.bot.settings["civilian_role"])
                
                # Update the roles
                await member.add_roles(lpd_role, recruit_role)
                try: await member.remove_roles(civilian_role)
                except discord.errors.HTTPException: pass
            bot_messages.append(await ctx.send("Everyone you mentioned has been added to cadet."))
            
            # Remove the users message
            result = await Confirm("Can I remove your message?").prompt(ctx)
            if result: await ctx.message.delete()

            # Remove all the bot messages
            for message in bot_messages: await message.delete()

class Other(commands.Cog):
    """Here are all the one off commands that I have created and are not apart of any group."""
    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.dark_magenta()
    
    @commands.command()
    async def role_to_vrc(self):
        """
        This command takes in a name of a role and outputs the VRC names of the people in it.

        This command ignores the decoration on the role if it has any and it also requires
        """