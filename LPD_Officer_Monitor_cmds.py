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

def getJsonFile(file_name):
    # Add the .json extention if it was not included in the file_name
    if file_name[-5::] != ".json": file_name += ".json"

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


# ====================
# Global Variables
# ====================

officer_manager = None
settings = getJsonFile("settings")
keys = getJsonFile("Keys")
help_dict = getJsonFile("help")


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
    global officer_manager
    print("on_ready")
    
    officer_manager = await OfficerManager.start(
        bot,
        settings,
        keys["SQL_Password"]
    )

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


# ====================
# Add cogs
# ====================

bot.add_cog(Time(bot, officer_manager))


# ====================
# Start
# ====================

bot.run(keys["Discord_token"])