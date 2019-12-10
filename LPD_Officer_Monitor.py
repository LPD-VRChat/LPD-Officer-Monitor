import discord
from discord.ext import commands
import os
import time
import asyncio
import copy
import datetime
import json
import emoji

def getJsonFile(file_name):
    # Add the .json extention if it was not included in the file_name
    if file_name[-5::] != ".json": file_name += ".json"

    # Get all the data out of the JSON file, parse it and return it
    with open(file_name, "r") as json_file:
        data = json.load(json_file)
    return data

settings = getJsonFile("settings")
commands = getJsonFile("help")

max_inactive_time_seconds = settings["max_inactive_days"] * 86400# Convert days to seconds


officer_monitor = {}

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
    except FileNotFoundError:
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

async def overwriteDBFile(officer_monitor_file):
    print("++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Writing to file\n")

    openFile = open(settings["storage_file_name"], "w")
    try:
        for ID in list(officer_monitor_file):
            openFile.write(str(ID)+","+str(officer_monitor_file[ID]["Last active time"])+","+str(officer_monitor_file[ID]["Time"])+"\n")
    except Exception as error: print("Something failed with writing to file:",error)
    finally: openFile.close()
    
    print("++++++++++++++++++++++++++++++++++++++++++++++++++")

async def removeUser(user_id):
    global officer_monitor

    print("88888888888888888888888888888888888888888888888888")
    print("Removing",client.get_user(int(user_id)),"from the officer_monitor\n")

    # Get the contents of the file
    officer_monitor_file = await readDBFile(settings["storage_file_name"])

    # Remove the user from officer_monitor_file
    try:
        del officer_monitor_file[user_id]
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
    await overwriteDBFile(officer_monitor_file)

    print("88888888888888888888888888888888888888888888888888")

async def logAllInfoToFile(guild):
    global officer_monitor
    print("||||||||||||||||||||||||||||||||||||||||||||||||||")
    print("Starting to log to file\n")
    
    database_officer_monitor = await readDBFile(settings["storage_file_name"])
    
    # Add missing users to officer_monitor
    for member in get_all_officers(guild):
        if str(member.id) not in officer_monitor:
            # Give the missing officer the time of 0
            officer_monitor[str(member.id)] = {"Time": 0}

            # Check if the officer has any last active time in the file, if so give him that time, otherwise just the current time
            try: officer_monitor[str(member.id)]["Last active time"] = database_officer_monitor[str(member.id)]["Last active time"]
            except KeyError:
                officer_monitor[str(member.id)]["Last active time"] = time.time()
                print(member.name,"was reset in the dict and got last active time from the current time")

    # Remove extra users from the officer_monitor
    for member in guild.members:
        

    # Making a copy of officer_monitor for logging to file
    officer_monitor_static = copy.deepcopy(officer_monitor)
    print("global officer_monitor cloned into officer_monitor_static")

    # Reset Officer Monitor on duty time
    for ID in list(officer_monitor):
        officer_monitor[ID]["Time"] = 0
    print("global officer_monitor reset")

    # Writing to file
    try:
        print("Opening file:",str(settings["storage_file_name"])+"...")
        # Writing info from last file and officer_monitor over previus data
        openFile = open(settings["storage_file_name"],"w")
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

    print("||||||||||||||||||||||||||||||||||||||||||||||||||")

async def getTopOrBottom(message, arguments, top):
    async with message.channel.typing():
        try:
            num1 = int(arguments[2])
            num2 = int(arguments[3])
        except IndexError:
            await sendErrorMessage(message, "You likely forgot to put both numbers, put two numbers after the command, one for where to start in the list, and then one for where to end.")
            return
        except TypeError:
            await sendErrorMessage(message, "The two last arguments must be whole numbers")
            return

        if num1 < 1:
            await sendErrorMessage(message, "The first number must be higher than or equal to 1")
            return

        combined_officer_monitor = copy.deepcopy(officer_monitor)
        database_officer_monitor = await readDBFile(settings["storage_file_name"])
        
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

                user = client.get_user(int(user_id))

                if user is not None:
                    await message.channel.send(str(i+1)+". "+user.mention + " | "+onDutyTime+" | "+str(datetime.datetime.utcfromtimestamp(combined_officer_monitor[user_id]["Last active time"]).strftime('%d.%m.%Y %H:%M:%S')))
        
        except IndexError:
            await sendErrorMessage(message, "Error - Make sure that you started at 1 or higher and ended at less or equal to all officers in the LPD")
            return

async def checkOfficerHealth(Guild_ID):
    await client.wait_until_ready()
    global officer_monitor
    if client.get_guild(Guild_ID) is not None:
        guild = client.get_guild(Guild_ID)
    else:
        print("Wrong Server_ID")
        await asyncio.sleep(settings["sleep_time_beetween_writes"])
        return


    while not client.is_closed():
        # Logging all info to file
        try:
            await logAllInfoToFile(guild)

            await asyncio.sleep(settings["sleep_time_beetween_writes"])
        except Exception as error:
            print("Something failed with logging to file")
            print(error)
            print("||||||||||||||||||||||||||||||||||||||||||||||||||")
            await asyncio.sleep(settings["sleep_time_beetween_writes"])

async def findInactiveOfficers(guild):
    global officer_monitor

    all_inactive_people = []

    # Check if someone has to be removed from the LPD because of inactivity
    for officer_id in list(officer_monitor):
        if officer_monitor[officer_id]["Last active time"] + max_inactive_time_seconds < time.time():
            officer = guild.get_member(int(officer_id))

            if officer is not None:
                all_inactive_people.append(officer)
    
    return all_inactive_people

async def goOnDuty(member, guild):
    global officer_monitor
    current_time = time.time()
    officer_monitor[str(member.id)]["Start time"] = current_time
    officer_monitor[str(member.id)]["Last active time"] = current_time

    on_duty_role = guild.get_role(settings["on_duty_role"])
    await member.add_roles(on_duty_role)

async def goOffDuty(member, guild):
    global officer_monitor
    current_time = time.time()
    try:
        officer_monitor[str(member.id)]["Time"] += int(current_time - officer_monitor[str(member.id)]["Start time"])
        print("Time in last channel:",str(int(current_time - officer_monitor[str(member.id)]["Start time"]))+"s by",member.name)
    except KeyError: print(member.name,"left an on duty voice channel and was not being monitored")
    officer_monitor[str(member.id)]["Last active time"] = current_time

    on_duty_role = guild.get_role(settings["on_duty_role"])
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

def isNumber(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

async def parseAnnouncement(message):
    # Parse the message and search for the date
    for word in message.content.split(" "):
        number_of_date_separators = 0
        date_separator = None
        for letter in word:
            if date_separator is None:
                if letter in settings["date_separators"]:
                    number_of_date_separators += 1
                    date_separator = letter
            else:
                if letter == date_separator:
                    number_of_date_separators += 1
        if number_of_date_separators == 2:
            temp_event_date = word.split(date_separator)
            try:
                if isNumber(temp_event_date[0]) and isNumber(temp_event_date[1]) and isNumber(temp_event_date[2][0:4]):
                    if int(temp_event_date[0]) <= 31 and int(temp_event_date[1]) <= 12:
                        event_date = temp_event_date
                        break
            except IndexError:
                pass
    else: return False
    
    event_date[2] = event_date[2][0:4]
    print(event_date)
    
    # Parse the message and search for the time
    event_time = False
    event_time_ending_pm = None
    UTC_zone = None
    for word in message.content.split(" "):
        if ("PM" in word or "AM" in word) and isNumber(word[0]):

            if isNumber(word[1]): event_time = int(word[0:2])
            else: event_time = int(word[0])

            if "PM" in word: event_time_ending_pm = True
            elif "AM" in word: event_time_ending_pm = False

        if "UTC" in word and word[-2] in ["+","-"] and isNumber(word[-1]):
            UTC_zone = int(word[-2::])
            break

    else: return False

    if event_time_ending_pm is True:
        event_time += 12

    print(event_time)
    print(UTC_zone)

    print("Embeding")

    dateAndTime = datetime.datetime(
        int(event_date[2]),
        int(event_date[1]),
        int(event_date[0]),
        event_time
    )
    dateAndTime += datetime.timedelta(hours=UTC_zone)

    color = discord.Colour.from_rgb(51, 153, 255)

    embed = discord.Embed(
        title="Time for the event:",
        colour=color,
        timestamp=dateAndTime
    )

    await message.channel.send(embed=embed)
    return True

def renewInactiveTime(member):
    global officer_monitor
    
    if str(member.id) in officer_monitor:
        officer_monitor[str(member.id)]["Last active time"] = time.time()
        return True
    else:
        return False

def getMemberStringFromMemberList(member_list):
    returnString = ""

    for member in member_list:
        print(member.name)
        print(member.name.find(":"))
        for letter in member.name:
            if letter in emoji.UNICODE_EMOJI:
                returnString = returnString + "`<@" + str(member.id) + ">`\n"
                break
        else:
            returnString = returnString + "@" + member.name + "#" + member.discriminator + "\n"
    
    return returnString

def get_category(category_id, guild):
    for category in guild.categories:
        if category.id == category_id:
            return category
    return None

def cmd_with_prefix(command):
    return settings["bot_prefix"]+command+" "

def get_all_officers(guild):

    all_officers = []

    for member in guild.members:
        for role in member.roles:
            if role.id in settings["role_ladder_id"]:
                all_officers.append(member)
    
    return all_officers

def has_officer_role(roles):
    for role in roles:
        if role.id in settings["role_ladder_id"]:
            return True
    return False

client = discord.Client()

@client.event
async def on_message(message):
    global officer_monitor


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


    # ------------------------------ Other channels ------------------------------

    # If the channel is in the list counted_channels than the last active time is updated in the officer_monitor for that officer
    if message.channel.name in settings["counted_channels"]:
        try:
            officer_monitor[str(message.author.id)]["Last active time"] = time.time()
            print("Message in",message.channel.name,"written by",message.author.name)
        except KeyError:
            print("The user",message.author.name,"is not in the officer_monitor and was sending a message to the",message.channel.name,"channel")

    # Add the time to event announcments
    if message.channel.name == "events-and-announcements":
        await parseAnnouncement(message)


    # ------------------------------ Admin Bot Channel Filters ------------------------------

    # Stop if the message is not in the admin bot channel
    if message.channel.id != settings["admin_bot_channel"]:
        return

    # Stop if their is no content in the message
    if message.content == "":
        return

    # Stop if the bot prefix is not in the message
    if message.content[0] != settings["bot_prefix"]:
        return

    # Create a variable with the command the user sent in
    user_command = message.content.split(" ")[0][1::]

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
            if not message.mentions:
                await sendErrorMessage(message, "You forgot to mention someone to get info about")
                return
            if message.author in message.mentions:
                await sendErrorMessage(message, "This feature is not for competing against other higherups, you don't need to know your own time.")
                return

            database_officer_monitor = await readDBFile(settings["storage_file_name"])
            
            for user in message.mentions:
                if str(user.id) not in officer_monitor:
                    await sendErrorMessage(message, user.mention+" is not being monitored, are you sure this is an LPD officer?")
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
                    

                    await message.channel.send(user.mention+" was last active "+str(datetime.datetime.utcfromtimestamp(unixTimeOfUserActive).strftime('%d.%m.%Y %H:%M:%S'))+" and the user has been on duty for:"+onDutyTime)

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

        elif arg2 == "reset":
            async with message.channel.typing():
                for officer_id in list(officer_monitor):
                    officer_monitor[officer_id]["Time"] = 0

                await overwriteDBFile(officer_monitor)

                await message.channel.send("The time for everyone has been cleared")

        elif arg2 == "dump":
            await logAllInfoToFile(message.guild)

            db_file = discord.File(settings["storage_file_name"], settings["storage_file_name"])

            await message.channel.send("Here is the database file:", file=db_file)

    elif user_command == "parse_announcement":
        announcement_channel = await getChannelByName("events-and-announcements", message.guild, True)

        old_message = None
        async for old_message_2 in announcement_channel.history(limit=1):
            old_message = old_message_2
            break

        worked = await parseAnnouncement(old_message)

        if worked is True: await message.channel.send("Last message parsed and the time/date have been added to it.")
        else: await message.channel.send("Last message parsed but the time/date were not found.")

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
async def on_voice_state_update(member, before, after):
    global officer_monitor

    # Get the guild
    try: guild = before.channel.guild
    except AttributeError: guild = after.channel.guild
    
    # Check if this is just a member and if it is than just return
    if not has_officer_role(member.roles): return
    
    if after.channel == before.channel: return# The user was just doing something inside a monitored voice channel
    
    # These check if an officer is entering or leaving a monitored voice channel, not moving.
    if before.channel is None:
        # An LPD Officer entered any voice channel
        if after.channel.category_id == settings["on_duty_category"]:
            # An LPD Officer is going on duty
            await goOnDuty(member, guild)
        return
    elif after.channel is None:
        # An LPD Officer left any voice channel
        if before.channel.category_id == settings["on_duty_category"]:
            # An LPD Officer is going off duty
            await goOffDuty(member, guild)
        return

    # Check where the officer was moving between
    if before.channel.category_id == settings["on_duty_category"] and after.channel.category_id == settings["on_duty_category"]:
        # An Officer moved between monitored voice channels
        return
    elif after.channel.category_id == settings["on_duty_category"]:
        # The officer moved from a voice channel that is not monitored to one that is monitored
        await goOnDuty(member, guild)
    elif before.channel.category_id == settings["on_duty_category"]:
        # The officer moved from a monitored voice channel to another one witch is not monitored
        await goOffDuty(member, guild)

@client.event
async def on_member_update(before, after):
    global officer_monitor

    officer_before = has_officer_role(before.roles)
    officer_after = has_officer_role(after.roles)

    # Nothing happened to an LPD Officer
    if officer_before is True and officer_before is True: return
    # Nothing happened to a regular member
    elif officer_before is False and officer_after is False: return
    
    # Member has joined the LPD
    elif officer_before is False and officer_after is True:
        officer_monitor[str(before.id)] = {"Time": 0,"Last active time": time.time()}# User added to the officer_monitor
        print(before.name,"added to the officer_monitor")

    # Member has left the LPD
    elif officer_before is True and officer_after is False:
        officer_monitor[str(before.id)]
        await removeUser(str(before.id))


client.loop.create_task(checkOfficerHealth(settings["Server_ID"]))

# This failes if it is run localy so that then it uses the local token.txt file
try: client.run(os.environ["DISCORD_TOKEN"])# This is for the heroku server
except KeyError: client.run(settings["Discord_token"])
