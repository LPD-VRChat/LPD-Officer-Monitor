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
import Classes.errors as errors
from Classes.commands import Time
from Classes.help_command import Help
from Classes.extra_functions import handle_error, get_settings_file


# ====================
# Argparse
# ====================

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--server", action="store_true")
args = parser.parse_args()


# ====================
# Global Variables
# ====================

if args.server:
    settings = get_settings_file("remote_settings")
    keys = get_settings_file("remote_keys")
else:
    settings = get_settings_file("settings")
    keys = get_settings_file("keys")

bot = commands.Bot(command_prefix=settings["bot_prefix"])
bot.settings = settings
bot.officer_manager = None


# ====================
# Checks
# ====================

@bot.check
def supports_dms(ctx):
    if ctx.guild is None:
        print("Direct messages not supported.")
        raise commands.NoPrivateMessage("This bot does not support direct messages.")
    else: return True

@bot.check
def officer_manager_ready(ctx):
    if ctx.bot.officer_manager is None: raise errors.NotReadyYet("I am still starting up, give me a moment.")
    else: return True

@bot.check
def in_admin_bot_channel(ctx):
    if ctx.channel.id == ctx.bot.settings["admin_bot_channel"]: return True
    else: raise errors.WrongChannelForCommand("This command only works in the administration bot channel.")


# ====================
# Discord Events
# ====================

@bot.event
async def on_ready():
    print("on_ready")
    global bot

    # Make sure this function does not create the officer manager twice
    if bot.officer_manager is not None: return

    # Start the officer manager
    print("Starting officer manager")
    bot.officer_manager = await OfficerManager.start(
        bot,
        keys["SQL_Password"]
    )

@bot.event
async def on_message(message):
    # print("on_message")

    # Only parse the commands if the message was sent in an allowed channel
    if message.channel.id in bot.settings["allowed_command_channels"]:
        await bot.process_commands(message)

    # Archive the message
    if message.channel.category_id not in bot.settings["monitored_channels"]["ignored_categories"] and bot.officer_manager != None:
        officer = bot.officer_manager.get_officer(message.author.id)
        if officer: await officer.log_message_activity(message)

@bot.event
async def on_voice_state_update(member, before, after):
    # print("on_voice_state_update")
    if bot.officer_manager is None: return
    
    # Get the officer
    officer = bot.officer_manager.get_officer(member.id)
    
    # Check if this is just a member and if it is than just return
    if officer is None: return
    
    if after.channel == before.channel: return# The user was just doing something inside a monitored voice channel
    
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
    if before.channel.category_id == bot.settings["on_duty_category"] and after.channel.category_id == bot.settings["on_duty_category"]:
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
    # print("on_member_uspdate")
    if bot.officer_manager is None: return

    officer_before = bot.officer_manager.is_officer(before)
    officer_after = bot.officer_manager.is_officer(after)

    # Nothing happened to an LPD Officer
    if officer_before is True and officer_after is True: return
    # Nothing happened to a regular member
    elif officer_before is False and officer_after is False: return
    
    # Member has joined the LPD
    elif officer_before is False and officer_after is True:
        await bot.officer_manager.create_officer(after.id)

    # Member has left the LPD
    elif officer_before is True and officer_after is False:
        await bot.officer_manager.remove_officer(before.id, reason = "this person does not have the LPD role anymore")

@bot.event
async def on_error(event, *args, **kwargs):
    print("on_error")
    await handle_error(bot, f"Error encountered in event: {event}", traceback.format_exc())

@bot.event
async def on_command_error(ctx, exception):
    print("on_command_error")

    exception_string = str(exception).replace("raised an exception", "encountered a problem")
    
    await ctx.send(exception_string)
    
    if exception_string.find("encountered a problem") != -1:
        await handle_error(bot, exception_string, "".join(traceback.format_exception(None, exception, None)))


# ====================
# Add cogs
# ====================

bot.remove_command("help")
bot.add_cog(Help(bot))
bot.add_cog(Time(bot))


# ====================
# Start
# ====================

# bot.loop.create_task(setup_officer_manager())
bot.run(keys["Discord_token"])