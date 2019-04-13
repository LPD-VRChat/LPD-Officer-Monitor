import discord
from discord.ext import commands

admin_channel = "admin-bot-channel"
bot_prefix = "?"
all_commands = [bot_prefix + x for x in ["help","who"]]
all_help_text =  [
    "Get info about all commands",
    "Get everyone in a voice channel in a list"
]
help_dict = {}
for i in range(0, len(all_commands)):
    help_dict[all_commands[i]] = all_help_text[i]

token_file_name = "token.txt"
print(help_dict)

def getToken():
    token_file = open(token_file_name, "r")
    token = token_file.read()
    token_file.close()
    return token

async def getChannelByName(name):
    channel_enumerator = client.get_all_channels()
    for channel in channel_enumerator:
        if channel.name == name:
            return channel
    return False

async def sendErrorMessage(message, text):
    await message.channel.send(message.author.mention+" "+str(text))


client = discord.Client()

@client.event
async def on_message(message):
    if message.content.split(" ")[0] not in all_commands:
        return

    if message.channel.name != admin_channel:
        admin_channel_local = await getChannelByName(admin_channel)

        if admin_channel_local is False:
            await message.channel.send("Please create a channel named "+admin_channel+" for the bot to use")
            return

        await message.channel.send("This bot does only work in "+admin_channel_local.mention)
        return

    if message.content.find(bot_prefix+"who") != -1:

        try:
            message.content[len(bot_prefix)+1+4]# This tests if the string is long enough to contain the channel name and if this is not it goes to the except IndexError
            argument = message.content[len(bot_prefix)+1+4::]# This does not throw an index error if the string is only 4 characters (no idea why)
        except IndexError:
            await sendErrorMessage(message, "There is a missing an argument. Do "+bot_prefix+"help for help")
            return

        channel = await getChannelByName(argument)
        
        if channel is False:
            await sendErrorMessage(message, "This channel does not exist.")
            return

        if not channel.members:
            await sendErrorMessage(message, channel.name+" is empty")
            return

        everyone_in_channel = ""
        for member in channel.members:
            everyone_in_channel = everyone_in_channel + "\n" + member.name
        await message.channel.send("Here is everyone in the channel "+channel.name+":"+everyone_in_channel)

    if message.content.find(bot_prefix+"help") != -1:
        try:
            message.content[len(bot_prefix)+1+4]# This tests if the string is long enough to contain the channel name and if this is not it goes to the except IndexError
            argument = message.content[len(bot_prefix)+1+4::]# This does not throw an index error if the string is only 4 characters (no idea why)
        except IndexError:
            all_text = "To get more information on how to use a specific command please use ?help and than put the command you want more info on after that"
            for command in help_dict:
                all_text = all_text+"\n"+command+": "+help_dict[command]

            await message.channel.send(all_text)

token = getToken()
client.run(token)

