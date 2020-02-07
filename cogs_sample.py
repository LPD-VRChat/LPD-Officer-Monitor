from discord.ext import commands
import commentjson as json


bot = commands.Bot(command_prefix='?')

class Time(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx, arg1):
        print("ctx:",ctx)
        await ctx.send(str(arg1))

bot.add_cog(Time(bot))


with open("keys.json", "r") as json_file:
    data = json.load(json_file)
bot.run(data["Discord_token"])