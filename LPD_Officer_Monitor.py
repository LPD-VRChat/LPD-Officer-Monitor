import discord
from discord.ext import commands
import os
import time
import asyncio
import copy
from datetime import datetime

class Help():
    def __init__(self, name, short_explanation, long_explanation):
        self.name = name
        self.command = bot_prefix + name
        self.short_explanation = short_explanation
        self.long_explanation = long_explanation

Server_ID = 446345091230072834
Others_excluded = [294518114903916545]
max_inactive_time_days = 28# In days
max_inactive_time_seconds = max_inactive_time_days * 86400# Convert days to seconds
manager_role = "Moderator"
storage_file_name = "LPD_database.csv"
main_role_name = "LPD"
counted_channels = ["lpd-chat", "looking-for-group", "events-and-announcements"]
join_up_channel = "join-up"
max_applications = 15
sleep_time_beetween_writes = 3600
voice_channel_being_monitored = "on duty"
admin_channel_name = "admin-bot-channel"
bot_prefix = "?"
settingsMessages = {
    "show_group_channels": 582330373095292950
}

commands = [
    Help("help",
        "Get info about all commands",
        "help gets general info about all commands if it is used without arguments but an argument can be send with it to get more specific information about a specific command. Example: "+bot_prefix+"help who"
    ),
    Help("who",
        "Get everyone in a voice channel in a list",
        "who gets a list of all people in a specific voice channel and can output the list with any seperator as long as the separator does not contain spaces. who needs two arguments, argument one is the separator and argument number 2 is the name of the voice channel. To make a tab you put /t and for enter you put /n. Example: "+bot_prefix+"who , General"
    ),
    Help("time",
        "Get how much time each officer has been in the "+voice_channel_being_monitored+" channel and how long they have been inactive",
        "time is the command to manage and get info about time spent in the on duty voice channel and how long officers have been inactive.\n-----\ntime user [@ the user/s] gets info about a specific user/users\n-----\ntime top [from number] [to number] this gets info about all officers and organizes them from people who have been to most on duty to the ones that have been the least on duty, for example if you want the top 10 do: "+bot_prefix+"time top 1 10\n-----\njust like time top but takes from the bottom\n-----\ntime renew [@ the user/s] updates last active time for all users mentioned in the message to the current time, Example: "+bot_prefix+"time renew @Hroi#1994 @HroiTest#2003\n-----\n!DEVELPER COMMAND time write writes all changes to file, this is manely used if the bot is going offline"
    ),
    Help("now",
        "Get the current time of the server",
        "now gives the current time of the server to calculate how far your own time zone is away from the servers time zone."
    )
]

officer_monitor = {}

token_file_name = "token.txt"

def getToken():
    token_file = open(token_file_name, "r")
    token = token_file.readline().replace("\n","")
    token_file.close()
    print('"'+token+'"')
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
    print("--------------------------------------------------")
    print("Reading from file\n")
    database_officer_monitor = {}
    print("officer_monitor created for data from file:",database_officer_monitor)

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

            database_officer_monitor[user_id] = {}
            database_officer_monitor[user_id]["Last active time"] = last_active_time
            database_officer_monitor[user_id]["Time"] = on_duty_time
    except Exception as error: print("Something failed with reading from file:",error)
    finally:
        openFile.close()
        print("officer_monitor read successfully from file")
    
    print("--------------------------------------------------")
    
    return database_officer_monitor

async def writeToDBFile(officer_monitor_local):
    print("++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Writing to file\n")

    openFile = open(storage_file_name, "w")
    try:
        for ID in list(officer_monitor_local):
            openFile.write(str(ID)+","+str(officer_monitor_local[ID]["Last active time"])+","+str(officer_monitor_local[ID]["Time"])+"\n")
    except Exception as error: print("Something failed with writing to file:",error)
    finally: openFile.close()
    
    print("++++++++++++++++++++++++++++++++++++++++++++++++++")

async def removeUser(user_id):
    global officer_monitor

    print("88888888888888888888888888888888888888888888888888")
    print("Removing",client.get_user(int(user_id)),"from the officer_monitor\n")

    # Get the contents of the file
    officer_monitor_local = await readDBFile(storage_file_name)

    # Remove the user from officer_monitor_local
    try:
        del officer_monitor_local[user_id]
        print("User removed from the officer_monitor file")
    except KeyError:
        print("Could not delete the user with the user id from officer_monitor file",user_id,"because the user does not exsist in the officer_monitor file (the officer must have been in the LPD for less than an hour")

    # Remove the user from the global officer_monitor
    try:
        del officer_monitor[user_id]
        print("User removed from the officer_monitor")
    except KeyError:
        print("Could not delete the user with the user id from officer_monitor",user_id,"because the user does not exsist in the officer_monitor")
        print("officer_monitor:",officer_monitor)

    # Write the changes to the file
    await writeToDBFile(officer_monitor_local)

    print("88888888888888888888888888888888888888888888888888")

async def logAllInfoToFile(guild):
    global officer_monitor
    print("||||||||||||||||||||||||||||||||||||||||||||||||||")
    print("Starting to log to file\n")
    
    database_officer_monitor = await readDBFile(storage_file_name)
    
    # Add missing users to officer_monitor
    main_role = await getRoleByName(main_role_name, guild)
    members_with_main_role = [member for member in guild.members if main_role in member.roles]
    for member in members_with_main_role:
        try:
            officer_monitor[str(member.id)]
        except KeyError:
            officer_monitor[str(member.id)] = {"Time": 0}
            try:
                officer_monitor[str(member.id)]["Last active time"] = database_officer_monitor[str(member.id)]["Last active time"]
            except KeyError:
                officer_monitor[str(member.id)]["Last active time"] = time.time()
                print(member.name,"was reset in the dict and got last active time from the current time")

    # Making a copy of officer_monitor for logging to file
    officer_monitor_static = copy.deepcopy(officer_monitor)
    print("global officer_monitor cloned into officer_monitor_static")

    # Reset Officer Monitor
    for ID in list(officer_monitor):
        officer_monitor[ID]["Time"] = 0
    print("global officer_monitor reset")

    # Writing to file
    try:
        print("Opening file:",str(storage_file_name)+"...")
        # Writing info from last file and officer_monitor over previus data
        openFile = open(storage_file_name,"w")
        print("File opened")

        for ID in list(officer_monitor_static):
            # Add the users stats togather and write it to the file
            try:# This is so that is a user is only created in the officer_monitor it will be added to the file without an error
                all_time = officer_monitor_static[ID]["Time"] + database_officer_monitor[ID]["Time"]
            except KeyError:
                all_time = officer_monitor_static[ID]["Time"]
            if "Last active time" in list(officer_monitor_static[ID]):
                last_active_time = officer_monitor_static[ID]["Last active time"]
            else:
                last_active_time = database_officer_monitor[ID]["Last active time"]
            
            openFile.write(ID+","+str(last_active_time)+","+str(all_time)+"\n")
        print("Everything written to file successfully")
    except Exception as error: print("Something failed with writing to file:",error)
    finally: openFile.close()

async def getTopOrBottom(message, arguments, top):
    async with message.channel.typing():
        try:
            num1 = int(arguments[2])
            num2 = int(arguments[3])
        except IndexError:
            await sendErrorMessage(message, "The userID is missing")
            return
        except TypeError:
            await sendErrorMessage(message, "The two last arguments must be whole numbers")
            return

        if num1 < 1:
            await sendErrorMessage(message, "The first number must be higher than or equal to 1")
            return

        combined_officer_monitor = copy.deepcopy(officer_monitor)
        database_officer_monitor = await readDBFile(storage_file_name)
        
        # Get the time from the file and add that to the time in the officer_monitor dict
        for userID in officer_monitor:
            try:
                combined_officer_monitor[userID]["Time"] += database_officer_monitor[userID]["Time"]
            except KeyError:
                pass
        print("combined_officer_monitor:\n",combined_officer_monitor)

        user_on_duty_time = {n: combined_officer_monitor[n]["Time"] for n in combined_officer_monitor}
        sortedUsersByTime = sorted(user_on_duty_time, key=user_on_duty_time.get)

        sortedUsersByTime = list(sortedUsersByTime)
        if top is True:
            sortedUsersByTime.reverse()

        try:
            await message.channel.send("Officer | on duty time | date\n")
            for i in range(num1 -1, num2):
                user_id = sortedUsersByTime[i]
                #Calculate days, hours, minutes and seconds
                onDutySeconds = combined_officer_monitor[user_id]["Time"]
                onDutyMinutes, onDutySeconds = divmod(onDutySeconds, 60)
                onDutyHours, onDutyMinutes = divmod(onDutyMinutes, 60)
                onDutyDays, onDutyHours = divmod(onDutyHours, 24)
                onDutyweeks, onDutyDays = divmod(onDutyDays, 7)

                onDutyTime = str(onDutyweeks) +":"+ str(onDutyDays) +":"+ str(onDutyHours) +":"+ str(onDutyMinutes) +":"+ str(onDutySeconds)

                await message.channel.send(client.get_user(int(user_id)).mention + " | "+onDutyTime+" | "+str(datetime.utcfromtimestamp(combined_officer_monitor[user_id]["Last active time"]).strftime('%d.%m.%Y %H:%M:%S')))
        except IndexError:
            await sendErrorMessage(message, "Error - Make sure that you started at 1 or higher and ended at less or equal to all officers in the LPD")

async def checkOfficerHealth(Guild_ID):
    await client.wait_until_ready()
    global officer_monitor
    if client.get_guild(Guild_ID) is not None:
        guild = client.get_guild(Guild_ID)
    else:
        print("Wrong Server_ID")
        await asyncio.sleep(sleep_time_beetween_writes)
        return


    while not client.is_closed():
        # Logging all info to file
        try:
            await logAllInfoToFile(guild)

            # Check if someone has to be removed from the LPD because of inactivity
            for officer in list(officer_monitor):
                if officer_monitor[officer]["Last active time"] + max_inactive_time_seconds < time.time():
                    # Check if the message has already been sent
                    try:
                        if officer_monitor[officer]["Reported"] is True:
                            print(client.get_user(int(officer)),"already reported")# user already reproted
                        else:
                            officer_monitor[officer]["Not a real key"]
                    except KeyError:# The user has not been reported
                        channel = await getChannelByName(admin_channel_name, guild, True)# Get the channel to send the message to
                        # Send the message
                        unixTimeOfUserActive = officer_monitor[officer]["Last active time"]
                        last_active_time_human_readable = str(datetime.utcfromtimestamp(unixTimeOfUserActive).strftime('%d.%m.%Y %H:%M:%S'))
                        
                        moderator = await getRoleByName(manager_role, guild)
                        if moderator.mentionable is True:
                            await channel.send(moderator.mention+" The user "+str(client.get_user(int(officer)))+" has been inactive for "+str(max_inactive_time_days)+" days and was last active "+last_active_time_human_readable)
                        else:
                            await channel.send("ERROR The role "+manager_role+" is not mentionable")
                            await channel.send("The user "+str(client.get_user(int(officer)))+" has been inactive for "+str(max_inactive_time_days)+" days and was last active "+last_active_time_human_readable)
                        officer_monitor[officer]["Reported"] = True

            print("||||||||||||||||||||||||||||||||||||||||||||||||||")

            await asyncio.sleep(sleep_time_beetween_writes)
        except Exception as error:
            print("Something failed with logging to file")
            print(error)
            print("||||||||||||||||||||||||||||||||||||||||||||||||||")
            await asyncio.sleep(sleep_time_beetween_writes)

async def goOnDuty(member, guild):
    global officer_monitor
    current_time = time.time()
    officer_monitor[str(member.id)]["Start time"] = current_time
    officer_monitor[str(member.id)]["Last active time"] = current_time

    on_duty_role = await getRoleByName(voice_channel_being_monitored, guild)
    await member.add_roles(on_duty_role)

async def goOffDuty(member, guild):
    global officer_monitor
    current_time = time.time()
    try:
        officer_monitor[str(member.id)]["Time"] += int(current_time - officer_monitor[str(member.id)]["Start time"])
        print("Time in last channel:",str(int(current_time - officer_monitor[str(member.id)]["Start time"]))+"s by",member.name)
    except KeyError: print(member.name,"left the voice channel and was not being monitored")
    officer_monitor[str(member.id)]["Last active time"] = current_time

    on_duty_role = await getRoleByName(voice_channel_being_monitored, guild)
    await member.remove_roles(on_duty_role)

async def removeJoinUpApplication(message, error_text, use_beginning_text = True):
    # Notify user that join up message did not get accepted
    if not message.author.dm_channel:
        await message.author.create_dm()
        
    if use_beginning_text is True: await message.author.dm_channel.send("Your application in "+message.channel.mention+" did not follow the template, "+error_text)
    else: await message.author.dm_channel.send(error_text)

    # Remove application
    await message.delete()

    return

        
client = discord.Client()

@client.event
async def on_message(message):
    global officer_monitor

    # Eliminate DM's
    try: message.channel.category_id
    except AttributeError:
        if message.channel.me != message.author:
            await message.channel.send("This bot does not support Direct Messages.")
        return

    # If the bot wrote the message it won't go further
    if message.author == message.guild.me:
        return

    # If the channel is in the list counted_channels than the last active time is updated in the officer_monitor for that officer
    if message.channel.name in counted_channels:
        try:
            officer_monitor[str(message.author.id)]["Last active time"] = time.time()
            print("Message in",message.channel.name,"written by",message.author.name)
        except KeyError:
            print("The user",message.author.name,"is not in the officer_monitor and was sending a message to the",message.channel.name,"channel")

    # Delete message if an LPD members sent to the channel #join-up
    if message.channel.name == join_up_channel:
        LPD_role = await getRoleByName(main_role_name, message.guild)
        Mod_role = await getRoleByName(manager_role, message.guild)

        # If the message is from a moderator, ignore the message
        if Mod_role in message.author.roles or message.author.id in Others_excluded or message.author.bot is True:
            return
        
        # Check if this message is from an LPD member, if so, remove it
        if LPD_role in message.author.roles:

            if not message.author.dm_channel:
                await message.author.create_dm()
            await message.author.dm_channel.send(main_role_name+" members cannot send to the "+message.channel.mention+" channel")
            
            await message.delete()
            return
        
        # This is a join up application

        # Make sure the message is the right length
        lines = message.content.count('\n') + 1
        if lines != 13:
            await removeJoinUpApplication(message, "please check the line spacing.")
            return

        # Make sure the person applying has not sent an application already
        # all_applications = 0
        async for old_message in message.channel.history(limit=None):
            if old_message.author == message.author and old_message.id != message.id:
                await removeJoinUpApplication(message, "You have already applied in "+message.channel.mention+", you cannot apply again until your application has been reviewed but you can edit your current application", False)
                return

        # This closes the applications after 15 applications but this feature was not accepted:
        #     if Mod_role not in old_message.author.roles and old_message.author.id not in Others_excluded and message.author.bot is not True:
        #         all_applications += 1
                
        # print(all_applications)
        
        # if all_applications >= max_applications:
        #     await message.channel.send("We are not accepting more applications until the current applications have been reivewed")
            
        #     # Lock the channel for the @everyone role
        #     everyone_role = await getRoleByName("@everyone", message.guild)
        #     overwrites = message.channel.overwrites
            
        #     if everyone_role in overwrites: overwrite = overwrites[everyone_role]
        #     else: overwrite = discord.PermissionOverwrite()

        #     overwrite.update(send_messages = False)

        #     await message.channel.set_permissions(everyone_role, overwrite=overwrite)


    # Check if the command exists, if not then send a message notifying someone that this message does not exist
    for command in commands:
        if message.content.split(" ")[0] == command.command:
            break
    else:
        return
    
    # If the channel name is not the admin_channel_name than reply with that the bot only works in the admin_channel_name channel
    if message.channel.name != admin_channel_name:
        admin_channel = await getChannelByName(admin_channel_name, message.guild, True)

        if admin_channel is False:
            await message.channel.send("Please create a text channel named "+admin_channel_name+" for the bot to use")
            return

        await message.channel.send("This bot does only work in "+admin_channel.mention)
        return

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
                everyone_in_channel = everyone_in_channel + separator + member.display_name
            else:
                everyone_in_channel += member.display_name
                has_run = True

        # This is to remove double backslashes witch discord adds to disable enter/tab functionality but I want that functunality here so I only want one of the backslashes
        everyone_in_channel = everyone_in_channel.replace("/t","\t")
        everyone_in_channel = everyone_in_channel.replace("/n","\n")
        
        await message.channel.send("Here is everyone in the voice channel "+channel.name+":\n"+everyone_in_channel)

    elif message.content.find(bot_prefix+"help") != -1:

        try:
            message.content[len(bot_prefix)+1+4]# This tests if the string is long enough to contain the channel name and if this is not it goes to the except IndexError
            argument = message.content[len(bot_prefix)+1+4::]# This does not throw an index error if the string is only 4 characters (no idea why)
        except IndexError:
            all_text = "To get more information on how to use a specific command please use ?help and than put the command you want more info on after that."
            for command in commands:
                all_text = all_text+"\n"+command.command+": "+command.short_explanation

            await message.channel.send(all_text)
            return

        for command in commands:
            if argument == command.name:
                # Command found
                await message.channel.send(command.long_explanation)
                break
        else:
            await sendErrorMessage(message, 'Help page not loaded because "'+argument+'" is not a valid command')
            return

    elif message.content.find(bot_prefix+"time") != -1:
        
        try:
            arguments = message.content.split(" ")
            arg2 = arguments[1]
        except IndexError:
            await sendErrorMessage(message, "Their is a missing argument do ?help for help")
            return

        if arg2 == "user":
            if not message.mentions:
                await sendErrorMessage(message, "You forgot to mention someone to get info about")
            
            database_officer_monitor = await readDBFile(storage_file_name)
            
            for user in message.mentions:
                if str(user.id) not in officer_monitor:
                    await sendErrorMessage(message, user.mention+" is not being monitored, are you sure this is an "+main_role_name+" officer?")
                else:
                    try:
                        onDutyTimeFromFile = database_officer_monitor[str(user.id)]["Time"]
                    except KeyError:
                        onDutyTimeFromFile = 0

                    # Get the time
                    unixTimeOfUserActive = officer_monitor[str(user.id)]["Last active time"]
                    onDutySeconds = officer_monitor[str(user.id)]["Time"] + onDutyTimeFromFile
                    #Calculate days, hours, minutes and seconds
                    onDutyMinutes, onDutySeconds = divmod(onDutySeconds, 60)
                    onDutyHours, onDutyMinutes = divmod(onDutyMinutes, 60)
                    onDutyDays, onDutyHours = divmod(onDutyHours, 24)
                    onDutyweeks, onDutyDays = divmod(onDutyDays, 7)

                    onDutyTime = ""
                    if onDutyweeks != 0:
                        onDutyTime += "\nWeeks: "+str(onDutyweeks)
                    if onDutyDays + onDutyweeks != 0:
                        onDutyTime += "\nDays: "+str(onDutyDays)
                    if onDutyHours + onDutyDays + onDutyweeks != 0:
                        onDutyTime += "\nHours: "+str(onDutyHours)
                    if onDutyMinutes + onDutyHours + onDutyDays + onDutyweeks != 0:
                        onDutyTime += "\nMinutes: "+str(onDutyMinutes)
                    onDutyTime += "\nSeconds: "+str(onDutySeconds)
                    

                    await message.channel.send(user.mention+" was last active "+str(datetime.utcfromtimestamp(unixTimeOfUserActive).strftime('%d.%m.%Y %H:%M:%S'))+" and the user has been on duty for:"+onDutyTime)

        elif arg2 == "write":
            await logAllInfoToFile(message.guild)
            await message.channel.send("Everything has been logged to file")

        elif arg2 == "top":
            await getTopOrBottom(message, arguments, True)
        
        elif arg2 == "bottom":
            await getTopOrBottom(message, arguments, False)

        elif arg2 == "renew":
            if not message.mentions:
                await sendErrorMessage(message, "You forgot to mention someone to renew their time")
        
            for user in message.mentions:
                if str(user.id) not in officer_monitor:
                    await sendErrorMessage(message, user.mention+" is not being monitored, are you sure this is an "+main_role_name+" officer?")
                else:
                    officer_monitor[str(user.id)]["Last active time"] = time.time()
                    await message.channel.send("Last active time for "+user.mention+" has been renewed")

@client.event
async def on_voice_state_update(member, before, after):
    global officer_monitor

    # Get teh guild
    try: guild = before.channel.guild
    except AttributeError: guild = after.channel.guild
    
    # Check if this is just a member and if it is than just return
    LPD_role = await getRoleByName(main_role_name, guild)
    if LPD_role not in member.roles:
        print("A normal member entered or exited a voice channel")
        return
    
    if after.channel == before.channel: return

    if before.channel is None:
        if after.channel.name == voice_channel_being_monitored or "group " in after.channel.name:
            # User comming on duty
            await goOnDuty(member, guild)

    elif after.channel is None:
        if before.channel.name == voice_channel_being_monitored or "group " in before.channel.name:
            # User comming off duty
            await goOffDuty(member, guild)

    else:# This runs if the user is going from one vocie channel to another
        if (after.channel.name == voice_channel_being_monitored or "group " in after.channel.name) and (before.channel.name != voice_channel_being_monitored and "group " not in before.channel.name):# Entering the channel being monitored
             # User comming on duty
            await goOnDuty(member, guild)
        elif (before.channel.name == voice_channel_being_monitored or "group " in before.channel.name) and (after.channel.name != voice_channel_being_monitored and "group " not in after.channel.name):# Exiting the channel being monitored
            # User comming off duty
            await goOffDuty(member, guild)

@client.event
async def on_member_update(before, after):
    global officer_monitor

    # Check if the member was entering or exiting the LPD role
    main_role = await getRoleByName(main_role_name,before.guild)

    if main_role in before.roles and main_role in after.roles:
        return
    elif main_role not in before.roles and main_role not in after.roles:
        return

    elif main_role not in before.roles and main_role in after.roles:# Member has joined the LPD
        officer_monitor[str(before.id)] = {"Time": 0,"Last active time": time.time()}# User added to the officer_monitor
        print(before.name,"added to the officer_monitor")

    elif main_role in before.roles and main_role not in after.roles:# Member has left the LPD
        officer_monitor[str(before.id)]
        await removeUser(str(before.id))

@client.event
async def on_raw_reaction_add(payload):
    if payload.message_id == settingsMessages["show_group_channels"]:
        # Show group channels
        member = client.get_user(payload.user_id)
        guild = client.get_guild(payload.guild_id)
        
        overwrite = discord.PermissionOverwrite()
        overwrite.update(read_messages = True)

        all_vocie_channels = guild.voice_channels
        for voice_channel in all_vocie_channels:
            if "group " in voice_channel.name:
                await voice_channel.set_permissions(member, overwrite=overwrite)
                print("Voice channel:",voice_channel.name,"has been enabled for",member.display_name)

@client.event
async def on_raw_reaction_remove(payload):
    if payload.message_id == settingsMessages["show_group_channels"]:
        # Hide group channels
        member = client.get_user(payload.user_id)
        guild = client.get_guild(payload.guild_id)
        
        overwrite = discord.PermissionOverwrite()
        overwrite.update(read_messages = None)

        all_vocie_channels = guild.voice_channels
        for voice_channel in all_vocie_channels:
            if "group " in voice_channel.name:
                await voice_channel.set_permissions(member, overwrite=overwrite)
                print("Voice channel:",voice_channel.name,"has been disabled for",member.display_name)

client.loop.create_task(checkOfficerHealth(Server_ID))

# This failes if it is run localy so that then it uses the local token.txt file
try: client.run(os.environ["DISCORD_TOKEN"])# This is for the heroku server
except KeyError:
    token = getToken()
    client.run(token)
