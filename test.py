import discord
import asyncio
import aiomysql
import datetime
import time
import json

# My Classes
from Classes.Officer import Officer
from Classes.OfficerManager import OfficerManager


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

def has_lpd_role(member):
    for role in member.roles:
        if role.id == settings["lpd_role"]:
            return True
    return False


# ====================
# Global Variables
# ====================

officer_manager = None
settings = getJsonFile("settings")
keys = getJsonFile("Keys")


# ====================
# Discord Events
# ====================

client = discord.Client()

# Load officer_manager and load all the officers to it
@client.event
async def on_ready():
    global officer_manager
    print("on_ready")
    
    officer_manager = await OfficerManager.start(
        client,
        settings["Server_ID"],
        settings["DB_name"],
        settings["DB_user"],
        settings["DB_host"],
        keys["SQL_Password"]
    )

@client.event
async def on_message(message):
    print("on_message")

    # Make sure the database and the officer list are ready
    if officer_manager is None: return

    print(officer_manager)
    officer = officer_manager.get_officer(566311811637575680)

    print("Officer:",officer)
    print("Is on duty:",officer.is_on_duty)

    print("On duty time before:", await officer.time())
    
    officer.go_on_duty()
    await asyncio.sleep(3.1)
    await officer.go_off_duty()

    print("On duty time after:", await officer.time())
    # from_date=(11, 1, 2020), to_date=(12, 1, 2020)

@client.event
async def on_member_update(before, after):
    print("on_member_update")
    
    officer_before = officer_manager.has_lpd_role(before)
    officer_after = officer_manager.has_lpd_role(after)

    # Nothing happened to someone
    if officer_before == officer_after: return

    # Member has joined the LPD
    elif officer_before is False and officer_after is True:
        await officer_manager.create_officer(before.id)

    # Member has left the LPD
    elif officer_before is True and officer_after is False:
        officer = officer_manager.get_officer(before.id)
        await officer.remove()

@client.event
async def on_voice_state_update(member, before, after):
    
    # Get the guild
    guild = officer_manager.guild
    
    # Filters
    # Just a regular member
    if officer_manager.is_officer(member) is False: return
    # Channel not changed
    elif after.channel == before.channel: return
    
    ##########################################################################################
    # This checks if an officer is entering or leaving a monitored voice channel, not moving.
    ##########################################################################################
    
    # An LPD Officer entered any voice channel
    if before.channel is None:
        # An LPD Officer is going on duty
        if after.channel.category_id == settings["on_duty_category"]:
            await officer_manager.get_officer(member.id).go_on_duty()
        return

    # An LPD Officer left any voice channel
    elif after.channel is None:
        # An LPD Officer is going off duty
        if before.channel.category_id == settings["on_duty_category"]:
            await officer_manager.get_officer(member.id).go_off_duty()
        return

    ##########################################################################################
    #                    This checks what channel an officer was moving between               
    ##########################################################################################
    
    # An Officer moved between monitored voice channels
    if before.channel.category_id == settings["on_duty_category"] and after.channel.category_id == settings["on_duty_category"]:
        return

    # The officer moved from a voice channel that is not monitored to one that is monitored
    elif after.channel.category_id == settings["on_duty_category"]:
        await officer_manager.get_officer(member.id).go_on_duty()

    # The officer moved from a monitored voice channel to another one witch is not monitored
    elif before.channel.category_id == settings["on_duty_category"]:
        await officer_manager.get_officer(member.id).go_off_duty()


# ====================
# Start the bot
# ====================

client.run(keys["Discord_token"])