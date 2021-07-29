# Settings import
import Settings

# Standard
import traceback
import asyncio
import argparse

# Community
import discord
from discord.ext import commands

# Mine
from BusinessLayer.extra_functions import handle_error
import BusinessLayer.checks as checks


class Programming(commands.Cog):
    def __init__(self, bot):
        self.bl_wrapper = bot.bl_wrapper
        self.color = discord.Color.red()

    @checks.is_team_bot_channel()
    @checks.is_programming_team()
    @commands.command()
    async def shutdown(self, ctx):
        """This command shuts the bot down cleanly"""
        await ctx.send("Shutting the bot down...")
        await self.bl_wrapper.clean_shutdown(
            "#" + ctx.channel.name, ctx.author.display_name, exit=True
        )

    @checks.is_team_bot_channel()
    @checks.is_programming_team()
    @commands.command()
    async def restart(self, ctx):
        """Restarts the bot if something is broken"""
        await ctx.send("Restarting the bot...")
        await self.bl_wrapper.clean_shutdown(
            "#" + ctx.channel.name, ctx.author.display_name, exit=False
        )

    @checks.is_team_bot_channel()
    @checks.is_programming_team()
    @commands.command()
    async def web(self, ctx):
        """web description"""
        pass

    @checks.is_team_bot_channel()
    @checks.is_programming_team()
    @commands.command()
    async def reload(self, ctx, module_name: str):
        """Reloads a module"""
        if module_name.lower() == "all":
            extensions = [name for name in self.bot.extensions.keys()]
            for m in extensions:
                try:
                    self.bot.reload_extension(m)
                    await ctx.send(f"""Successfull reloaded {m.split('.')[-1]}""")
                except Exception as e:
                    await ctx.send(f"""Failed to reload {m.split('.')[-1]}""")
                    await handle_error(self.bot, e, traceback.format_exc())
                print(
                    f"{ctx.author.display_name} reloaded {m.split('.')[-1]} from #{ctx.channel.name}"
                )
        else:
            module = f"UILayer.DiscordCommands.{module_name}"
            try:
                self.bot.reload_extension(module)
                await ctx.send(f"Successfully reloaded {module_name}")
                print(
                    f"{ctx.author.display_name} reloaded {module_name} from #{ctx.channel.name}"
                )
            except discord.ext.commands.errors.ExtensionNotLoaded:
                await ctx.send(
                    f"Could not find a module matching the name `{module_name}`"
                )
            except Exception as e:
                await ctx.send(f"Failed to reload `{module_name}`")
                await handle_error(self.bot, e, traceback.format_exc())


def setup(bot):
    bot.add_cog(Programming(bot))
