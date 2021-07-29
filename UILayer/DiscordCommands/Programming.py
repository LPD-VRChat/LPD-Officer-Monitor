# Settings import
import Settings

# Standard
import traceback
import asyncio
import argparse
import logging

# Community
import discord
from discord.ext import commands

# Mine
from BusinessLayer.extra_functions import handle_error
import BusinessLayer.checks as checks


log = logging.getLogger("lpd-officer-monitor")


class Programming(commands.Cog):
    def __init__(self, bot):
        self.bl_wrapper = bot.bl_wrapper
        self.bot = bot
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
        try:
            # Set the BL Wrapper to the bot so that it can be used during cog startup
            self.bot.bl_wrapper = self.bl_wrapper

            if module_name.lower() == "all":
                extensions = [name for name in self.bot.extensions.keys()]
                for m in extensions:
                    try:
                        self.bot.reload_extension(m)
                        await ctx.send(f"Successfull reloaded {m.split('.')[-1]}")
                    except Exception as e:
                        await ctx.send(f"Failed to reload `{module_name}`")
                        log.exception(f"Failed to reload {m.split('.')[-1]}")
                    finally:
                        log.warning(
                            f"{ctx.author.display_name} reloaded {m.split('.')[-1]} from #{ctx.channel.name}"
                        )
            else:
                module = f"UILayer.DiscordCommands.{module_name}"
                try:
                    self.bot.reload_extension(module)
                    await ctx.send(f"Successfully reloaded {module_name}")
                except discord.ext.commands.errors.ExtensionNotLoaded:
                    await ctx.send(
                        f"Could not find a module matching the name `{module_name}`"
                    )
                except Exception as e:
                    await ctx.send(f"Failed to reload `{module_name}`")
                    log.exception(f"Failed to reload {module_name}")
                finally:
                    log.warning(
                        f"{ctx.author.display_name} reloaded {module_name} from #{ctx.channel.name}"
                    )
        finally:
            # Remove the BL from the bot to prevent it from being used in the wrong places
            del self.bot.bl_wrapper


def setup(bot):
    bot.add_cog(Programming(bot))
