import discord
from discord.ext import commands
import json


# ====================
# Global Variables
# ====================




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


# ====================
# Discord Events
# ====================

bot = commands.Bot(command_prefix='?')

# Add all the officers
@bot.event
async def on_ready():
    print("on_ready")


# ====================
# Discord Commands
# ====================

@commands.command()
async def who(ctx, arg, arg2):
    print(arg)
    print(arg2)
    print(ctx)


bot.add_command(who)


# ====================
# Start the bot
# ====================

bot.run()