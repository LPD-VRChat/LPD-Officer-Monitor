import discord
from discord.ext import commands
import os
import time
import json
import asyncio
import copy
from datetime import datetime

Server_ID = 566315650864381953
storage_file_name = "LPD_database.csv"
main_role_name = "LPD"
counted_channels = ["lpd-chat", "looking-for-group"]
sleep_time_beetween_writes = 10
name_of_voice_channel_being_monitored = "on duty"
admin_channel = "admin-bot-channel"
bot_prefix = "?"
all_commands_no_prefix = ["help", "who", "time"]
all_commands = [bot_prefix + x for x in all_commands_no_prefix]
all_help_text =  [
    "Get info about all commands",
    "Get everyone in a voice channel in a list",
    "Get how much time each officer has been in the "+name_of_voice_channel_being_monitored+" channel"
]
all_help_text_long = [
    "help gets general info about all commands if it is used without arguments but an argument can be send with it to get more specific information about a specific command. Example: "+bot_prefix+"help who",
    "who gets a list of all people in a specific voice channel and can output the list with any seperator as long as the separator does not contain spaces. who needs two arguments, argument one is the separator and argument number 2 is the name of the voice channel. To make a tab you put /t and for enter you put /n. Example: "+bot_prefix+"who , General"
    "time ..."
]
help_dict = {}
for i in range(0, len(all_commands)):
    help_dict[all_commands[i]] = all_help_text[i]

officer_monitor = {}

token_file_name = "token.txt"

def getToken():
    token_file = open(token_file_name, "r")
    token = token_file.read()
    token_file.close()
    return token

async def getChannelByName(name, guild, text_channel):
    if text_channel == True: channels = guild.text_channels
    else: channels = guild.voice_channels

    for channel in channels:
        if channel.name == name:
            return channel
    else:
        return False

async def getRoleByName(name, guild):
    for role in guild.roles:
        if role.name == name:
            return role
    else:
        return False

async def sendErrorMessage(message, text):
    await message.channel.send(message.author.mention+" "+str(text))

async def readDBFile(fileName):# Reading all info about users from file
    database_officer_monitor = {}
    print("Extra officer_monitor created:",database_officer_monitor)

    # This makes it so that if their is no file it creates the file and then reads from the empty file
    try: openFile = open(fileName, "r")
    except IOError:
        # Creating the file
        openFile = open(fileName, "w")
        openFile.write("")
        openFile.close()
        # Opening the file again
        openFile = open(fileName, "r")

    try:
        for line in openFile:
            variables = line.split(",")

            user_id = str(variables[0])
            last_active_time = float(variables[1])
            on_duty_time = int(variables[2])
            
            # print("------------------------------")
            # print("user_id:",user_id)
            # print("last_active_time:",last_active_time)
            # print("on_duty_time:",on_duty_time)
            # print("------------------------------")

            database_officer_monitor[user_id] = {}
            database_officer_monitor[user_id]["Last active time"] = last_active_time
            database_officer_monitor[user_id]["Time"] = on_duty_time
    except Exception as error: print("Something failed with reading from file:",error)
    finally:
        openFile.close()
        print("database_officer_monitor after read:",database_officer_monitor)
    
    return database_officer_monitor

async def writeToDBFile(officer_monitor_local):
    openFile = open(storage_file_name, "w")
    try:
        for ID in list(officer_monitor_local):
            openFile.write(str(ID)+","+str(officer_monitor_local[ID]["Last active time"])+","+str(officer_monitor_local[ID]["Time"])+"\n")
    except Exception as error: print("Something failed with writing to file:",error)
    finally: openFile.close()

async def removeUser(user_id):
    global officer_monitor

    # Get the contents of the file
    officer_monitor_local = await readDBFile(storage_file_name)

    # Remove the user from officer_monitor_local
    try:
        del officer_monitor_local[user_id]
    except KeyError:
        print("Could not delete the user with the user id from officer_monitor_local",user_id,"because the user does not exsist in officer_monitor_local")
        print("officer_monitor_local:",officer_monitor_local)

    # Remove the user from the global officer_monitor
    try:
        del officer_monitor[user_id]
    except KeyError:
        print("Could not delete the user with the user id from officer_monitor",user_id,"because the user does not exsist in the officer_monitor")
        print("officer_monitor:",officer_monitor)

    # Write the changes to the file
    await writeToDBFile(officer_monitor_local)

async def checkOfficerHealth(Guild_ID):
    await client.wait_until_ready()
    global officer_monitor
    if client.get_guild(Guild_ID) is not None:
        guild = client.get_guild(Guild_ID)
    else:
        await asyncio.sleep(sleep_time_beetween_writes)
        return


    while not client.is_closed():
        # Logging all info to file
        try:
            print("||||||||||||||||||||||||||||||||||||||||||||||||||")
            print("Starting to log to file\n")
            
            database_officer_monitor = await readDBFile(storage_file_name)
            
            # Add missing users to officer_monitor
            main_role = await getRoleByName(main_role_name, guild)
            print("main_role name:",main_role.name)
            members_with_main_role = [member for member in guild.members if main_role in member.roles]
            print("members_with_main_role:",members_with_main_role)

            print("1. officer_monitor:",officer_monitor)
            
            for member in members_with_main_role:
                try:
                    officer_monitor[str(member.id)]
                    print(member.name,"excists in the dict")
                except KeyError:
                    officer_monitor[str(member.id)] = {"Time": 0}
                    try:
                        officer_monitor[str(member.id)]["Last active time"] = database_officer_monitor[str(member.id)]["Last active time"]
                    except KeyError:
                        officer_monitor[str(member.id)]["Last active time"] = time.time()
                    print(member.name,"was reset and has time 0 in the dict")
            
            print("Survived loop")
            print("2. officer_monitor:",officer_monitor)

            # for member in members_with_main_role: officer_monitor[str(member.id)] = {"Time": 0, "Last active time": time.time()}
            
            # Making a copy of officer_monitor for logging to file
            officer_monitor_static = copy.deepcopy(officer_monitor)
            print("officer_monitor cloned")

            print("3. officer_monitor:",officer_monitor)
            print("officer_monitor_static 1:",officer_monitor_static)

            # Reset Officer Monitor
            for ID in list(officer_monitor):
                officer_monitor[ID]["Time"] = 0
            
            print("officer_monitor reset")
            print("officer_monitor_static 2:",officer_monitor_static)

            try:
                print("Opening file:",storage_file_name)
                # Writing info from last file and officer_monitor over previus data
                openFile = open(storage_file_name,"w")
                print("File opened")

                print("officer_monitor_static:",officer_monitor_static)
                print("List of officer_monitor_static:",list(officer_monitor_static))

                for ID in list(officer_monitor_static):
                    print("Looping through the ID:",ID)
                    if ID not in list(database_officer_monitor):# The user was not in the read file
                        # Create the line for the user from the ground up
                        print("The user",client.get_user(int(ID)),"is not in the database")
                        print("Time:",officer_monitor_static[ID]["Time"])
                        
                        openFile.write(ID+","+str(officer_monitor_static[ID]["Last active time"])+","+str(officer_monitor_static[ID]["Time"])+"\n")

                    else:# The user was in the read file
                        # Add the users stats togather and write it to the file
                        print("The user",client.get_user(int(ID)),"is in the database")

                        all_time = officer_monitor_static[ID]["Time"] + database_officer_monitor[ID]["Time"]
                        if "Last active time" in list(officer_monitor_static[ID]):
                            print("Using last active time from dict")
                            last_active_time = officer_monitor_static[ID]["Last active time"]
                        else:
                            print("Using last active time from a file")
                            last_active_time = database_officer_monitor[ID]["Last active time"]
                        
                        openFile.write(ID+","+str(last_active_time)+","+str(all_time)+"\n")
            except Exception as error: print("Something failed with writing to file:",error)
            finally: openFile.close()

            # Check if someone has to be removed from the LPD because of inactivity

            await asyncio.sleep(sleep_time_beetween_writes)
        except Exception as error:
            print("Something failed with logging to file")
            print(error)
            await asyncio.sleep(sleep_time_beetween_writes)
        print("||||||||||||||||||||||||||||||||||||||||||||||||||")

        
client = discord.Client()

@client.event
async def on_message(message):
    global officer_monitor

    try: message.channel.category_id
    except AttributeError:
        if message.channel.me != message.author:
            await message.channel.send("This bot does not support Direct Messages.")
            return

    if message.content.split(" ")[0] not in all_commands:
        return

    if message.channel.name != admin_channel:
        admin_channel_local = await getChannelByName(admin_channel, message.guild, True)

        if admin_channel_local is False:
            await message.channel.send("Please create a text channel named "+admin_channel+" for the bot to use")
            return

        await message.channel.send("This bot does only work in "+admin_channel_local.mention)
        return

    if message.channel.name in counted_channels:
        officer_monitor[str(message.author.id)]["Last active time"] = time.time()
        print("Message in",message.channel.name,"written by",message.author.name)

    if message.content.find(bot_prefix+"who") != -1:

        try:
            arguments = message.content.split(" ")
            separator = arguments[1]
            channel_name = arguments[2::]
            channel_name = "".join([" "+x for x in channel_name])
            channel_name = channel_name[1::]
        except IndexError:
            await sendErrorMessage(message, "There is a missing an argument. Do "+bot_prefix+"help for help")
            return

        channel = await getChannelByName(channel_name, message.guild, False)
        
        if channel is False:
            await sendErrorMessage(message, "The channel "+channel_name+" does not exist or is not a voice channel.")
            return

        if not channel.members:
            await sendErrorMessage(message, channel.name+" is empty")
            return

        everyone_in_channel = ""
        has_run = False
        for member in channel.members:
            if has_run is True:
                everyone_in_channel = everyone_in_channel + separator + member.name
            else:
                everyone_in_channel += member.name
                has_run = True

        # This is to remove double backslashes witch discord adds to disable enter/tab functionality but I want that functunality here so I only want one of the backslashes
        everyone_in_channel = everyone_in_channel.replace("/t","\t")
        everyone_in_channel = everyone_in_channel.replace("/n","\n")
        
        await message.channel.send("Here is everyone in the voice channel "+channel.name+":\n"+everyone_in_channel)

    if message.content.find(bot_prefix+"help") != -1:

        try:
            message.content[len(bot_prefix)+1+4]# This tests if the string is long enough to contain the channel name and if this is not it goes to the except IndexError
            argument = message.content[len(bot_prefix)+1+4::]# This does not throw an index error if the string is only 4 characters (no idea why)
        except IndexError:
            all_text = "To get more information on how to use a specific command please use ?help and than put the command you want more info on after that."
            for command, explanation in help_dict.items():
                all_text = all_text+"\n"+command+": "+explanation

            await message.channel.send(all_text)
            return

        if argument not in all_commands_no_prefix:
            await sendErrorMessage(message, 'Help page not loaded because "'+argument+'" is not a valid command')
            return

        await message.channel.send(all_help_text_long[all_commands_no_prefix.index(argument)])

    if message.content.find(bot_prefix+"time") != -1:
        
        try:
            arguments = message.content.split(" ")
            arg2 = arguments[1]
        except IndexError:
            await sendErrorMessage(message, "Their is a missing argument")
            return
        
        # This is an outdated command witch has no use anymore
        # if arg2 == "reset":
        #     officer_monitor = {}

        #     main_role = await getRoleByName(main_role_name, message.guild)
        #     members_with_main_role = [member for member in message.guild.members if main_role in member.roles]

        #     for member in members_with_main_role: officer_monitor[str(member.id)] = {"Time": 0, "Last active time": time.time()}

        #     await message.channel.send("Time reset")

        if arg2 == "status":
            await message.channel.send(str(officer_monitor))
            return

        if arg2 == "user":
            try: userID = arguments[2]
            except IndexError:
                await sendErrorMessage(message, "The userID is missing")
                return
            
            database_officer_monitor = await readDBFile(storage_file_name)
            try:
                onDutyTimeFromFile = database_officer_monitor[userID]["Time"]
            except KeyError:
                onDutyTimeFromFile = 0
            
            if client.get_user(int(userID)) is None:
                await sendErrorMessage(message, "Their is no user in this server with the ID: "+str(userID))
                return

            unixTimeOfUserActive = officer_monitor[userID]["Last active time"]
            onDutyTime = officer_monitor[userID]["Time"] + onDutyTimeFromFile
            await message.channel.send(str(client.get_user(int(userID)))+" was last active "+str(datetime.utcfromtimestamp(unixTimeOfUserActive).strftime('%d.%m.%Y %H:%M:%S'))+" and the user has been on duty for "+str(onDutyTime)+"s")

@client.event
async def on_voice_state_update(member, before, after):
    global officer_monitor

    try: channel_being_monitored = await getChannelByName(name_of_voice_channel_being_monitored, before.channel.guild, False)
    except AttributeError: channel_being_monitored = await getChannelByName(name_of_voice_channel_being_monitored, after.channel.guild, False)
    
    if after.channel == before.channel: return
    if before.channel != channel_being_monitored and after.channel != channel_being_monitored: return
    
    current_time = time.time()

    if after.channel == channel_being_monitored and before.channel != channel_being_monitored:# Entering the channel being monitored
        officer_monitor[str(member.id)]["Start time"] = current_time
        officer_monitor[str(member.id)]["Last active time"] = current_time

    elif before.channel == channel_being_monitored and after.channel != channel_being_monitored:# Exiting the channel being monitored
        officer_monitor[str(member.id)]["Time"] += int(current_time - officer_monitor[str(member.id)]["Start time"])
        officer_monitor[str(member.id)]["Last active time"] = current_time
        print("Time in last channel:",str(int(current_time - officer_monitor[str(member.id)]["Start time"]))+"s")

@client.event
async def on_member_update(before, after):
    global officer_monitor

    print("Something changed!!!")

    main_role = await getRoleByName(main_role_name,before.guild)
    print("Main role:",main_role)

    print("main_role in before.roles:",main_role in before.roles)

    if main_role not in before.roles and main_role in after.roles:# Member has joined the LPD
        officer_monitor[str(before.id)] = {"Time": 0,"Last active time": time.time()}# User added to the officer_monitor
        print(before.name,"added to the officer_monitor")

    elif main_role in before.roles and main_role not in after.roles:# Member has left the LPD
        officer_monitor[str(before.id)]
        print("Removing",before.name,"from the officer_monitor")
        await removeUser(str(before.id))

client.loop.create_task(checkOfficerHealth(Server_ID))

# This failes if it is run localy so that then it uses the local token.txt file
try: client.run(os.environ["DISCORD_TOKEN"])# This is for the heroku server
except KeyError:
    token = getToken()
    client.run(token)
