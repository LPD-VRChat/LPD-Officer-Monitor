# ====================
# Imports
# ====================

# Standard
import asyncio
import datetime
import time
import sys
import traceback

# Community
import aiomysql
import discord
from discord.ext import commands
import commentjson as json

# Mine
from Classes.Officer import Officer
from Classes.OfficerManager import OfficerManager
import Classes.errors as errors
from Classes.commands import *


# ====================
# Functions
# ====================

def get_settings_file(settings_file_name, in_settings_folder = True):
    
    # Add the stuff to the settings_file_name to make it link to the right file
    file_name = settings_file_name+".json"

    # Add the settings folder to the filename if nececery
    if in_settings_folder: file_name = "settings/" + file_name

    # Get all the data out of the JSON file, parse it and return it
    with open(file_name, "r") as json_file:
        data = json.load(json_file)
    return data

async def handleError(*text, end=" "):
    error_text = "***ERROR***\n\n"
    for line in text: error_text += str(line) + end
    error_text += "\n" + traceback.format_exc()

    print(error_text)

    channel = bot.get_channel(settings["error_log_channel"])
    try:
        await channel.send(error_text)
    except discord.InvalidArgument:
        await channel.send("***I ENCOUNTERED AN ERROR AND THE ERROR MESSAGE DOES NOT FIT IN DISCORD.***")

async def setup_officer_manager():
    global officer_manager

    # This loop waits for the bot to start up before running the code inside it
    while True:

        # Make sure this function does not run until the bot is ready
        if bot_ready is False:
            await asyncio.sleep(.5)
            continue

        # Start the officer manager
        officer_manager = await OfficerManager.start(
            bot,
            settings,
            keys["SQL_Password"]
        )

        # Add cogs that need the officer manager
        bot.add_cog(Time(bot, officer_manager))
        
        # Make sure to exit the loop
        break


# ====================
# Global Variables
# ====================

bot_ready = False
officer_manager = None
settings = get_settings_file("settings")
keys = get_settings_file("Keys")
help_dict = get_settings_file("help", in_settings_folder = False)


# ====================
# Checks
# ====================

bot = commands.Bot(command_prefix='?')

@bot.check
def supports_dms(ctx):
    if ctx.guild is None:
        print("Direct messages not supported.")
        raise commands.NoPrivateMessage("This bot does not support direct messages.")
    else: return True

@bot.check
def officer_manager_ready(ctx):
    if officer_manager is None:
        print("Officer Monitor not ready.")
        raise errors.NotReadyYet("I am still starting up, give me a moment.")
    else: return True


# ====================
# Discord Events
# ====================

@bot.event
async def on_ready():
    print("on_ready")

    global bot_ready
    bot_ready = True

@bot.event
async def on_message(message):
    print("on_message")
    await bot.process_commands(message)

@bot.event
async def on_error(event, *args, **kwargs):
    print("on_error")
    await handleError("Error encountered in event: ", event)

@bot.event
async def on_command_error(ctx, exception):
    print("on_command_error")

    exception_string = str(exception).replace("raised an exception", "encountered a problem")
    
    await ctx.send(exception_string)

    if exception_string.find("encountered a problem") != -1:
        err_channel = bot.get_channel(settings["error_log_channel"])
        error_string = "***ERROR***\n\n"+exception_string+"\n"+str(traceback.format_exception(None, exception, None))
        print(error_string)
        await err_channel.send(error_string)


# ====================
# Add cogs
# ====================




# ====================
# Start
# ====================

bot.loop.create_task(setup_officer_manager())
bot.run(keys["Discord_token"])