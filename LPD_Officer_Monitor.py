import discord
from discord.ext import commands
import os

admin_channel = "admin-bot-channel"
bot_prefix = "?"
all_commands_no_prefix = ["help","who"]
all_commands = [bot_prefix + x for x in all_commands_no_prefix]
all_help_text =  [
    "Get info about all commands",
    "Get everyone in a voice channel in a list"
]
all_help_text_long = [
    "help gets general info about all commands if it is used without arguments but an argument can be send with it to get more specific information about a specific command. Example: "+bot_prefix+"help who",
    "who gets a list of all people in a specific voice channel and can output the list with any seperator as long as the separator does not contain spaces. who needs two arguments, argument one is the separator and argument number 2 is the name of the voice channel. To make a tab you put /t and for enter you put /n. Example: "+bot_prefix+"who , General"
]
help_dict = {}
for i in range(0, len(all_commands)):
    help_dict[all_commands[i]] = all_help_text[i]

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
    return False

async def sendErrorMessage(message, text):
    await message.channel.send(message.author.mention+" "+str(text))


client = discord.Client()

@client.event
async def on_message(message):

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
            for command in help_dict:
                all_text = all_text+"\n"+command+": "+help_dict[command]

            await message.channel.send(all_text)
            return

        if argument not in all_commands_no_prefix:
            await sendErrorMessage(message, 'Help page not loaded because "'+argument+'" is not a valid command')
            return

        await message.channel.send(all_help_text_long[all_commands_no_prefix.index(argument)])


# This failes if it is run localy so that then it uses the local token.txt file
try: client.run(os.environ["DISCORD_TOKEN"])# This is for the heroku server
except KeyError:
    token = getToken()
    client.run(token)
