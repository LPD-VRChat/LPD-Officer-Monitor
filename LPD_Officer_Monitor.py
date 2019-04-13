import discord
from discord.ext import commands

admin_channel = "admin-bot-channel"
bot_prefix = "?"
token_file_name = "token.txt"


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
    if message.channel.name != admin_channel:
        await message.channel.send("This bot does only work in ")
        return

    if message.content.find(bot_prefix+"who") != -1:

        try:
            message.content[5]# This tests if the string is long enough to contain the channel name and if this is not it goes to the except IndexError
            argument = message.content[5::]# This does not throw an index error if the string is only 4 characters (no idea why)
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
        pass

token = getToken()
client.run(token)

