import discord
from discord.ext import commands

admin_channel = "admin-bot-channel"
bot_prefix = "?"


token_file_name = "token.txt"
def saekjaToken():
    token_file = open(token_file_name, "r")
    token = token_file.read()
    token_file.close()
    return token

async def sendErrorMessage(message, text):
    await message.channel.send(message.author.mention+" "+str(text))


client = discord.Client()

# @client.event
# async def on_ready():
#     print('Started up as:',bot.user.name)

@client.event
async def on_message(message):
    if message.content.find(bot_prefix+"who") != -1 and message.channel.name == admin_channel:

        try:
            argument = message.content[5::]
        except IndexError:
            await sendErrorMessage(message, "There is a missing argument. Do "+bot_prefix+"help for help")

        channel_enumerator = client.get_all_channels()
        channel_found = False
        # channel = False
        for channel in channel_enumerator:
            if channel.name == argument:
                channel_found = True
                break
        
        if channel_found is True:
            everyone_in_channel = ""
            for member in channel.members:
                everyone_in_channel = everyone_in_channel + "\n" + member.name
            await message.channel.send("Here is everyone in the channel "+channel.name+":"+everyone_in_channel)

        else: await sendErrorMessage(message, "This channel does not exist.")
        

token = saekjaToken()
client.run(token)

