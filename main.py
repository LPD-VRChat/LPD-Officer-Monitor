# ====================
# Imports
# ====================

# Standard
import asyncio
import datetime
import time
import sys
import traceback
import argparse

# Community
import aiomysql
import discord
from discord.ext import commands
import commentjson as json

# Mine
from Classes.Officer import Officer
from Classes.OfficerManager import OfficerManager

from Classes.VRChatUserManager import VRChatUserManager

from Classes.commands import Time, VRChatAccoutLink, Applications, Other
from Classes.help_command import Help
from Classes.extra_functions import handle_error, get_settings_file
import Classes.errors as errors


# Set intents for the bot - this allows the bot to see other users in the server
intents = discord.Intents.default()
intents.members = True

# ====================
# Argparse
# ====================

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--server", action="store_true")
parser.add_argument("-l", "--local", action="store_true")
args = parser.parse_args()


# ====================
# Global Variables
# ====================

if args.server:
    settings = get_settings_file("Presets/remote_settings")
    keys = get_settings_file("Presets/remote_keys")
elif args.local:
    settings = get_settings_file("Presets/local_settings")
    keys = get_settings_file("Presets/local_keys")
else:
    settings = get_settings_file("settings")
    keys = get_settings_file("keys")

bot = commands.Bot(
    command_prefix=settings["bot_prefix"], intents=intents
)  # 10/12/2020 - Destructo added intents
bot.settings = settings
bot.officer_manager = None
bot.everything_ready = False


# ====================
# Checks
# ====================


@bot.check
def supports_dms(ctx):
    if ctx.guild is None:
        print("Direct messages not supported.")
        raise commands.NoPrivateMessage("This bot does not support direct messages.")
    else:
        return True


@bot.check
def officer_manager_ready(ctx):
    if ctx.bot.officer_manager is None:
        raise errors.NotReadyYet("I am still starting up, give me a moment.")
    else:
        return True


# ====================
# Discord Events
# ====================


@bot.event
async def on_ready():
    print("on_ready")
    global bot

    # Make sure this function does not create the officer manager twice
    if bot.officer_manager is not None:
        return

    # Create the function to run before officer removal
    async def before_officer_removal(bot, officer_id):
        await bot.user_manager.remove_user(officer_id)

    # Start the officer manager
    print("Starting officer manager")
    bot.officer_manager = await OfficerManager.start(
        bot, keys["SQL_Password"], run_before_officer_removal=before_officer_removal
    )

    # Start the VRChatUserManager
    bot.user_manager = await VRChatUserManager.start(bot)

    # Mark everything ready
    bot.everything_ready = True


@bot.event
async def on_message(message):
    # print("on_message")

    # Early out if message from the bot itself
    if message.author.bot:
        return

    # Private message are ignored
    if isinstance(message.channel, discord.DMChannel) or isinstance(message.channel, discord.GroupChannel):
        await message.channel.send("I'm just a robot")
        return

    # Only parse the commands if the message was sent in an allowed channel
    if message.channel.id in bot.settings["allowed_command_channels"]:
        await bot.process_commands(message)

    # If the message was sent in the #leave-of-absence channel, process it
    if message.channel.id == bot.settings["leave_of_absence_channel"]:
        await process_loa(message)

    # Archive the message
    if (
        message.channel.category_id
        not in bot.settings["monitored_channels"]["ignored_categories"]
        and bot.officer_manager != None
    ):
        officer = bot.officer_manager.get_officer(message.author.id)
        if officer:
            await officer.log_message_activity(message)


@bot.event
async def on_voice_state_update(member, before, after):
    # print("on_voice_state_update")
    if bot.officer_manager is None:
        return

    # Get the officer
    officer = bot.officer_manager.get_officer(member.id)

    # Check if this is just a member and if it is than just return
    if officer is None:
        return

    if after.channel == before.channel:
        return  # The user was just doing something inside a monitored voice channel

    # These check if an officer is entering or leaving a monitored voice channel, not moving.
    if before.channel is None:
        # An LPD Officer entered any voice channel
        if after.channel.category_id == bot.settings["on_duty_category"]:
            # An LPD Officer is going on duty
            officer.go_on_duty()
        return
    elif after.channel is None:
        # An LPD Officer left any voice channel
        if before.channel.category_id == bot.settings["on_duty_category"]:
            # An LPD Officer is going off duty
            await officer.go_off_duty()
        return

    # Check where the officer was moving between
    if (
        before.channel.category_id == bot.settings["on_duty_category"]
        and after.channel.category_id == bot.settings["on_duty_category"]
    ):
        # An Officer moved between monitored voice channels
        return
    elif after.channel.category_id == bot.settings["on_duty_category"]:
        # The officer moved from a voice channel that is not monitored to one that is monitored
        officer.go_on_duty()
    elif before.channel.category_id == bot.settings["on_duty_category"]:
        # The officer moved from a monitored voice channel to another one witch is not monitored
        await officer.go_off_duty()


@bot.event
async def on_member_update(before, after):

    if bot.officer_manager is None:
        return

    ############################
    # Check status of officers #
    ############################

    officer_before = bot.officer_manager.is_officer(before)
    officer_after = bot.officer_manager.is_officer(after)

    # Nothing happened to an LPD Officer
    if officer_before is True and officer_after is True:
        return
    # Nothing happened to a regular member
    elif officer_before is False and officer_after is False:
        return

    # Member has joined the LPD
    elif officer_before is False and officer_after is True:
        await bot.officer_manager.create_officer(after.id)

    # Member has left the LPD
    elif officer_before is True and officer_after is False:
        await bot.officer_manager.remove_officer(
            before.id, reason="this person does not have the LPD role anymore"
        )


@bot.event
async def on_member_remove(member):
    if bot.officer_manager.is_officer(member):
        await bot.officer_manager.remove_officer(
            member.id, reason="this person left the server."
        )


@bot.event
async def on_error(event, *args, **kwargs):
    print("on_error")
    await handle_error(
        bot, f"Error encountered in event: {event}", traceback.format_exc()
    )


@bot.event
async def on_raw_message_delete(payload):
    if payload.channel_id == bot.settings["leave_of_absence_channel"]:
        await bot.officer_manager.send_db_request(f"DELETE FROM LeaveTimes WHERE request_id = {payload.message_id}")
    
@bot.event
async def on_raw_bulk_message_delete(payload):
    if payload.channel_id == bot.settings["leave_of_absence_channel"]:
        for each in payload.message_ids:
            await bot.officer_manager.send_db_request(f"DELETE FROM LeaveTimes WHERE request_id = {each}")


@bot.event
async def on_command_error(ctx, exception):
    print("on_command_error")

    exception_string = str(exception).replace(
        "raised an exception", "encountered a problem"
    )

    # Send the reason for the error into the channel the user sent the command in,
    # if the bot does not have permission to do do so it will send an error message
    # into bot-debug-channel.
    try:
        await ctx.send(exception_string)
    except discord.Forbidden:
        bot.get_channel(settings["error_log_channel"]).send(
            f"**I do not have permission to send messages in {ctx.channel.mention}**"
        )
        pass

    if exception_string.find("encountered a problem") != -1:
        await handle_error(
            bot,
            exception_string,
            "".join(traceback.format_exception(None, exception, None)),
        )


async def save_loa(officer_id, date_start, date_end, reason, request_id, approved=1):
    """
    Pass all 4 required fields to save_loa()
    If record with matching officer_id is found,
    record will be updated with new dates and reason.
    """
    
    await bot.officer_manager.send_db_request(f"REPLACE INTO `LeaveTimes` (`officer_id`,`date_start`,`date_end`,`reason`,`request_id`,`approved`) VALUES ({officer_id},'{date_start}','{date_end}','{reason}',{request_id},{approved})")


async def process_loa(message):

    # Try and parse the message to get a useful date range
    officer_id = message.author.id
    try:
        date_range = message.content.split(":")[0]
        date_a = date_range.split("-")[0]
        date_b = date_range.split("-")[1]
        date_start = ["", "", ""]
        date_end = ["", "", ""]
        date_start[0] = date_a.split("/")[0].strip()
        date_start[1] = date_a.split("/")[1].strip()
        date_start[2] = date_a.split("/")[2].strip()
        date_end[0] = date_b.split("/")[0].strip()
        date_end[1] = date_b.split("/")[1].strip()
        date_end[2] = date_b.split("/")[2].strip()
        reason = message.content.split(":")[1].strip()
        months = dict(
            JAN=1,
            FEB=2,
            MAR=3,
            APR=4,
            MAY=5,
            JUN=6,
            JUL=7,
            AUG=8,
            SEP=9,
            OCT=10,
            NOV=11,
            DEC=12,
        )
        int(date_start[0])
        int(date_end[0])
        
        try:
            int(date_start[1])
        except:
            date_start[1] = date_start[1].upper()[0:3]
            date_start[1] = months[date_start[1]]

        try:
            int(date_end[1])
        except:
            date_end[1] = date_end[1].upper()[0:3]
            date_end[1] = months[date_end[1]]
  
    except:
        # If all of that failed, let the user know with an autodeleting message
        await message.channel.send(
            message.author.mention
            + " Please use correct formatting: 21/July/2020 - 21/August/2020: Reason.",
            delete_after=10,
            )
        await message.delete()
        return

    
    date_start = [int(i) for i in date_start]
    date_end = [int(i) for i in date_end]

    if date_start[1] < 1 or date_start[1] > 12 or date_end[1] < 1 or date_end[1] > 12:
        # If the month isn't 1-12, let the user know they dumb
        await message.channel.send(
            message.author.mention + " There are only 12 months in a year.",
            delete_after=10,
        )
        await message.delete()
        return

    # Convert our separate data into a usable datetime
    date_start_complex = (
        str(date_start[0]) + "/" + str(date_start[1]) + "/" + str(date_start[2])
    )
    date_end_complex = (
        str(date_end[0]) + "/" + str(date_end[1]) + "/" + str(date_end[2])
    )
    date_start = datetime.datetime.strptime(date_start_complex, "%d/%m/%Y")
    date_end = datetime.datetime.strptime(date_end_complex, "%d/%m/%Y")

    if date_end > date_start + datetime.timedelta(
        weeks=+12
    ) or date_end < date_start + datetime.timedelta(weeks=+4):
        # If more than 12 week LOA, inform user
        await message.channel.send(
            message.author.mention
            + " Leaves of Absence are limited to 4-12 weeks. For longer times, please contact a White Shirt (Lieutenant or Above).",
            delete_after=10,
        )
        await message.delete()
        return

    # Fire the script to save the entry
    request_id = message.id
    await save_loa(officer_id, date_start, date_end, reason, request_id)
    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')

# ====================
# Add cogs
# ====================

bot.remove_command("help")
bot.add_cog(Help(bot))
bot.add_cog(Time(bot))
bot.add_cog(VRChatAccoutLink(bot))
bot.add_cog(Applications(bot))
bot.add_cog(Other(bot))


# ====================
# Start
# ====================

bot.run(keys["Discord_token"])
