# ====================
# Imports
# ====================

# Standard
import asyncio
import datetime
import json
import time

# Community
import aiomysql
import discord

# Mine
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

async def sendErrorMessage(message, text):
    await message.channel.send(message.author.mention+" "+str(text))

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


# ====================
# Global Variables
# ====================

officer_manager = None
settings = getJsonFile("settings")
keys = getJsonFile("Keys")
commands = getJsonFile("help")


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
        settings,
        keys["SQL_Password"]
    )

@client.event
async def on_message(message):
    print("on_message")

    # Make sure the database and the officer list are ready
    if officer_manager is None: return


    # ------------------------------ Start filters ------------------------------

    # Eliminate DM's
    try: message.channel.category_id
    except AttributeError:
        if message.channel.me != message.author:
            await message.channel.send("This bot does not support Direct Messages.")
        return

    # If the bot wrote the message it won't go further
    if message.author == message.guild.me:
        return


    # ------------------------------ Setup Variables ------------------------------

    officer = officer_manager.get_officer(message.author.id)


    # ------------------------------ Other channels ------------------------------

    # If the channel is in the list counted_channels than the last active time is updated in the officer_monitor for that officer
    # TODO: Log the message that was sent if it was in a tracked channel

    # Add the time to event announcments - Discontinued -
    # Not sure if this feature will be enabled again because it hasn't really been used too much,
    # if it will be enabled again it will have to be made easier to use.

    # Automatic role assignment after training
    # if message.channel.id == settings["training_finished_channel"]:

    #     # Check what rank people are requesting
    #     if message.content.lower().find("recruit") != -1:

    #         # Make sure the officer requesting rank is already a cadet
    #         if officer is None:
    #             await message.channel.send(message.author.mention+" I can't see you in the LPD, are you sure you are already a cadet?")


    #         # Make sure only one trainer is mentioned
    #         if len(message.mentions) == 0:
    #             await message.channel.send(message.author.mention+" you need to mention who trained you.")
    #             return
            
    #         elif len(message.mentions) == 1:
            
    #             trainer = officer_manager.get_officer(message.mentions[0].id)
                
    #             # Make sure the person training is an LPD Officer and a trainer
    #             if trainer is None:
    #                 await message.channel.send(message.author.mention+" I can't find the person you mentioned, are you sure they are in the LPD?")
    #                 return
    #             if trainer.is_trainer:
    #                 await message.channel.send(message.author.mention+" I can't see the person you mentioned as a trainer, are you sure you mentioned the right person?")
    #                 return

    #             # Make sure the people requesting recruit rank does not already have it
    #             if officer.is_trained:
    #                 await message.channel.send(message.author.mention+" you are already a recruit or higher.")
    #                 return

    #             # Add the reaction
    #             await message.add_reaction("✅")

    #         elif len(message.mentions) > 1:
    #             await message.channel.send(message.author.mention+" please only mention one trainer.")
    #             return
        
    #     else: await message.channel.send(message.author.mention+" I did not find what rank you are requesting, please check your spelling and make sure to request a rank in the correct format.")
        

    # ------------------------------ Admin Bot Channel Filters ------------------------------

    # Stop if the message is not in the admin bot channel
    if message.channel.id != settings["admin_bot_channel"]: return

    # Stop if their is no content in the message
    if message.content == "": return

    # Stop if the bot prefix is not in the message
    if message.content[0:len(settings["bot_prefix"])] != settings["bot_prefix"]: return

    # Create a variable with the command the user sent in
    user_command = message.content.split(" ")[0][len(settings["bot_prefix"])::]

    # Check if the command exists, if not then send a message notifying someone that this message does not exist
    if user_command not in commands:
        await sendErrorMessage(message, "The command you put in does not exist, check how you spelled it.")
        return


    # ------------------------------ Commands ------------------------------

    if user_command == "who":

        try:
            arguments = message.content.split(" ")
            arg2 = arguments[1]
        except IndexError:
            await sendErrorMessage(message, "There is a missing an argument. Do "+settings["bot_prefix"]+"help who to get help for this command")
            return

        if arg2 == "channel":
            try:
                channel_name = arguments[2::]
                channel_name = "".join([" "+x for x in channel_name])
                channel_name = channel_name[1::]

                print("Channel name: ",channel_name)
            except IndexError:
                await sendErrorMessage(message, "Make sure to include a name for the channel you want to get the time for.")
                return

            channel = await getChannelByName(channel_name, message.guild, False)
        
            if channel is False:
                await sendErrorMessage(message, "The channel "+channel_name+" does not exist or is not a voice channel.")
                return
            if not channel.members:
                await sendErrorMessage(message, channel.name+" is empty")
                return

            everyone_in_channel = getMemberStringFromMemberList(channel.members)
            await message.channel.send("Here is everyone in the voice channel "+channel.name+":\n"+everyone_in_channel)
            return

        elif arg2 == "on_duty":
            on_duty_category = get_category(settings["on_duty_category"], message.guild)
            everyone_on_duty = []
            
            for voice_channel in on_duty_category.voice_channels:
                for member in voice_channel.members:
                    print("Adding someone")
                    everyone_on_duty.append(member)

            print("Checking if everyone_on_duty is empty: ",everyone_on_duty)
            if not everyone_on_duty:
                await sendErrorMessage(message, "Their is no one on duty.")
                return

            everyone = getMemberStringFromMemberList(everyone_on_duty)
            await message.channel.send("Here is everyone who is on duty:\n"+everyone)

    elif user_command == "help":
        
        # The user put in a specific command to get info about
        try:
            # This stops the program if the argument is not a command
            command = message.content.split(" ")[1]
            try:
                commands[command]
            except KeyError:
                await sendErrorMessage(message, "Their is no command with the name "+command)
                return

            if isinstance(commands[command]["long_description"], dict):

                embed = discord.Embed(
                    title=settings["bot_prefix"]+command,
                    description=cmd_with_prefix(command)+commands[command]["long_description"]["description"],
                    colour=discord.Colour.from_rgb(0, 163, 255)
                )

                for part in commands[command]["long_description"]["commands"]:

                    command_name = u"\u2063"+"\n"+cmd_with_prefix(command)+part
                    command_description = commands[command]["long_description"]["commands"][part]

                    embed.add_field(
                        name=command_name,
                        value=command_description,
                        inline=False
                    )

            else:

                embed = discord.Embed(
                    title=settings["bot_prefix"]+command,
                    description=cmd_with_prefix(command)+commands[command]["long_description"],
                    colour=discord.Colour.from_rgb(0, 163, 255)
                )

            await message.channel.send(embed=embed)

        # The command dosn't have arguments and will give general information about all commands
        except IndexError:
            embed = discord.Embed(
                title="All commands:",
                description="To get more information about a specific command do "+settings["bot_prefix"]+"help command",
                colour=discord.Colour.from_rgb(0, 163, 255)
            )

            for command in commands:
                embed.add_field(
                    name=u"\u2063"+"\n"+settings["bot_prefix"]+command,
                    value=commands[command]["short_description"],
                    inline=False
                )
            
            await message.channel.send(embed=embed)

    elif user_command == "time":
        
        try:
            arguments = message.content.split(" ")
            arg2 = arguments[1]
        except IndexError:
            await sendErrorMessage(message, "Their is a missing argument do ?help for help")
            return

        if arg2 == "user":
            
            # Send an error message if no one is mentioned
            if not message.mentions:
                await sendErrorMessage(message, "You forgot to mention someone to get info about")
                return
            # Send an error message if the author mentioned himself
            if message.author in message.mentions:
                await sendErrorMessage(message, "This feature is not for competing against other higherups, you don't need to know your own time.")
                return
            
            # Give time info about all users mentioned in the message
            for user in message.mentions:
                # get the current officer
                current_officer = officer_manager.get_officer(user.id)

        if arg2 == "user":
            # Send an error message if no one is mentioned
            if not message.mentions:
                await sendErrorMessage(message, "You forgot to mention someone to get info about")
                return
            # Send an error message if the author mentioned himself
            if message.author in message.mentions:
                await sendErrorMessage(message, "This feature is not for competing against other higherups, you don't need to know your own time.")
                return
            
            # Give time info about all users mentioned in the message
            for user in message.mentions:
                # get the current officer
                current_officer = officer_manager.get_officer(user.id)

                # Make sure the officer is being tracked
                if current_officer is None:
                    await sendErrorMessage(message, user.mention+" is not being monitored, are you sure this is an LPD officer?")
                    return

                # Get the time
                on_duty_time = await current_officer.get_time_days()
                on_duty_time_string = seconds_to_string(on_duty_time)
                
                # Get last activity
                last_activity = await get_last_activity()

                # Send the message
                await message.channel.send(user.mention+" was last active "+last_activity+" and the user has been on duty for:"+on_duty_time_string)

        elif arg2 == "top":
            await getTopOrBottom(message, arguments, True)
        
        elif arg2 == "bottom":
            await getTopOrBottom(message, arguments, False)

        elif arg2 == "renew":
            if not message.mentions:
                await sendErrorMessage(message, "You forgot to mention someone to renew their time")
        
            for user in message.mentions:
                result = renewInactiveTime(user)
                
                if result: await message.channel.send("Last active time for "+user.mention+" has been renewed")
                else: await sendErrorMessage(message, user.mention+" is not being monitored, are you sure this is an LPD officer?")

        elif arg2 == "inactive":
            all_inactive_officers = await findInactiveOfficers(message.guild)

            if not all_inactive_officers:
                await message.channel.send("Their is no one inactive in the LPD, it is a good day today.")
                return
            
            for officer in all_inactive_officers:
                inactive_days = int((time.time() - officer_monitor[str(officer.id)]["Last active time"]) / 86400)

                unixTimeOfUserActive = officer_monitor[str(officer.id)]["Last active time"]
                last_active_time_human_readable = str(datetime.datetime.utcfromtimestamp(unixTimeOfUserActive).strftime('%d.%m.%Y %H:%M:%S'))

                await message.channel.send(officer.mention+" has been inactive for "+str(inactive_days)+" days and was last active "+last_active_time_human_readable)

        elif arg2 == "dump":
            await logAllInfoToFile(message.guild)

            db_file = discord.File(settings["storage_file_name"], settings["storage_file_name"])

            await message.channel.send("Here is the database file:", file=db_file)

    elif user_command == "count_officers":
        
        # Get all officers to count them
        all_officers = get_all_officers(message.guild)
        number_of_officers = len(all_officers)
        
        # Get a Dictionary ready that will contain number of officers with each role
        number_of_officers_with_each_role = {}
        for role_id in settings["role_ladder_id"]:# This goes through each item in the role_ladder_id list, finds the role and then adds it to a dictionary to be counted
            role = message.guild.get_role(role_id)

            if role is None:
                await sendErrorMessage(message, "The role with the ID "+str(role_id)+" was not found")
                return
            
            number_of_officers_with_each_role[role] = 0

        # This goes through each officer and checkes what rank they have, if a rank is found the program adds one to that item in the dictionary and breaks to check the next officer        
        for officer in all_officers:
            for role in number_of_officers_with_each_role:
                if role in officer.roles:
                    number_of_officers_with_each_role[role] += 1
                    break
        
        # Create the embed with number of officers
        embed = discord.Embed(
            title="Number of all LPD officers: "+str(number_of_officers),
            colour=discord.Colour.from_rgb(255, 255, 0)
        )

        # Add feilds with each role to the embed
        for role in number_of_officers_with_each_role:
            
            if role.name[0:4] == "LPD ": name = role.name[4::] + "s"
            else: name = role.name

            embed.add_field(name=name+":", value=number_of_officers_with_each_role[role])

        await message.channel.send(embed=embed)

    elif user_command == "add_inactive_officers":

        inactive_role = await getRoleByName(settings["inactive_role"], message.guild)
        
        if inactive_role is False:
            await sendErrorMessage(message, 'The role "'+settings['inactive_role']+'" does not exist')
            return

        for officer in await findInactiveOfficers(message.guild):
            print("Adding officer to the inactive role:",officer)
            await officer.add_roles(inactive_role)

        await message.channel.send("All inactive officers have been added to the role "+inactive_role.name)

    elif user_command == "accept_all_inactive_resons":
        inactive_channel = await getChannelByName(settings["inactive_channel_name"], message.guild, True)
        inactive_role = await getRoleByName(settings["inactive_role"], message.guild)

        officers_removed = 0
        officers_kicked_for_inactivity = inactive_role.members
        async for old_message in inactive_channel.history(limit=None):
            if inactive_role in old_message.author.roles:
                await old_message.author.remove_roles(inactive_role, reason="The officer has replied in the inactive channel with a reason.")# Remove the inactive role
                
                result = renewInactiveTime(old_message.author)# Renew the time
                if result is False: await sendErrorMessage(message, "The time of "+old_message.author+" who wrote this message could not be updated for some reason:\n```\n"+old_message.content+"\n```")# Let the user know if the time for someone did not get renewed
                
                officers_removed += 1
                
                if old_message.author in officers_kicked_for_inactivity:
                    officers_kicked_for_inactivity.remove(old_message.author)# Remove the officer from the list witch contains everyone who has to be removed

        await message.channel.send(str(officers_removed)+" officers have been removed from the inactive role and their time has been renewed")
        
        inactive_officers_needing_removal = ""
        for old_member in officers_kicked_for_inactivity:
            inactive_officers_needing_removal += old_member.mention
            inactive_officers_needing_removal += "\n"
        await message.channel.send("Here is everyone who has to be removed for inactivity:\n"+inactive_officers_needing_removal)

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
    print("on_voice_state_update")
    
    # Filters
    # The person is not being monitored by the bot
    if officer_manager.is_monitored(member.id) is False:
        print("Regular member doing something")
        return
    # Channel not changed
    elif after.channel == before.channel:
        print("Channel not changed")
        return
    
    ##########################################################################################
    # This checks if an officer is entering or leaving a monitored voice channel, not moving.
    ##########################################################################################
    
    # An LPD Officer entered any voice channel
    if before.channel is None:
        # An LPD Officer is going on duty
        if after.channel.category_id == settings["on_duty_category"]:
            try: officer_manager.get_officer(member.id).go_on_duty()
            except TypeError: print("ERROR The member",member.name+"#"+member.discriminator,"is not being monitored but is going on duty")
        return

    # An LPD Officer left any voice channel
    elif after.channel is None:
        # An LPD Officer is going off duty
        if before.channel.category_id == settings["on_duty_category"]:
            try: await officer_manager.get_officer(member.id).go_off_duty()
            except TypeError: print("ERROR The member",member.name+"#"+member.discriminator," is not being monitored but is going off duty")
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
