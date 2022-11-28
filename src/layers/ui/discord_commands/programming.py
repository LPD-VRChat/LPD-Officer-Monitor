# Settings import
import settings

# Standard
import traceback
import asyncio
import argparse
import logging
from typing import Optional
import importlib
import sys

# Community
import discord
from discord.ext import commands, menus

# Custom
import src.layers.business.checks as checks
from src.layers.business.bl_wrapper import BusinessLayerWrapper
from src.layers.business.extra_functions import send_long
from src.layers import business as bl


log = logging.getLogger("lpd-officer-monitor")

class Confirm(menus.Menu):
    def __init__(
        self, msg, timeout=30.0, delete_message_after=True, clear_reactions_after=False
    ):
        super().__init__(
            timeout=timeout,
            delete_message_after=delete_message_after,
            clear_reactions_after=clear_reactions_after,
        )
        self.msg = msg
        self.result = None

    async def send_initial_message(self, ctx, channel):
        return await channel.send(self.msg)

    @menus.button("\N{WHITE HEAVY CHECK MARK}")
    async def do_confirm(self, payload):
        self.result = True
        self.stop()

    @menus.button("\N{CROSS MARK}")
    async def do_deny(self, payload):
        self.result = False
        self.stop()

    async def prompt(self, ctx):
        await self.start(ctx, wait=True)
        return self.result


class Programming(commands.Cog):
    def __init__(self, bot):
        self.bl_wrapper: BusinessLayerWrapper = bot.bl_wrapper
        self.bot = bot
        self.color = discord.Color.red()

    @checks.is_team_bot_channel()
    @checks.is_programming_team()
    @commands.command()
    async def shutdown(self, ctx):
        """This command shuts the bot down cleanly"""
        await ctx.send("Shutting the bot down...")
        await self.bl_wrapper.p.clean_shutdown(
            "#" + ctx.channel.name, ctx.author.display_name, exit=True
        )

    @checks.is_team_bot_channel()
    @checks.is_programming_team()
    @commands.command()
    async def restart(self, ctx):
        """Restarts the bot if something is broken"""
        await ctx.send("Restarting the bot...")
        await self.bl_wrapper.p.clean_shutdown(
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
    async def reload(self, ctx, module_name: Optional[str] = None):
        """Reloads a module"""
        try:
            # Set the BL Wrapper to the bot so that it can be used during cog startup
            self.bot.bl_wrapper = self.bl_wrapper

            if module_name is None or module_name.lower() == "all":
                # copy dict because one failed load will change the dictionary
                loadedModules = sys.modules.copy()
                try:
                    for name, module in loadedModules.items():
                        if name.startswith("settings"):
                            importlib.reload(module)
                except Exception as e:
                    await ctx.send(f"Failed to reload settings")
                    log.exception(f"Failed to reload settings")
                    return
                try:
                    for name, module in loadedModules.items():
                        if name.startswith("src.layers.business"):
                            print(name)
                            importlib.reload(module)
                except Exception as e:
                    await ctx.send(f"Failed to reload business layer")
                    log.exception(f"Failed to reload business layer")
                    return

                mm_bl = bl.mm_bl.MemberManagementBL(self.bot)
                pt_bl = bl.pt_bl.PatrolTimeBL(self.bot)
                vrc_bl = bl.VRChatBL()
                p_bl = bl.ProgrammingBL(self.bot)
                web_bl = self.bot.bl_wrapper.web  # bl.WebManagerBL(self.bot)
                mod_bl = bl.ModerationBL(self.bot)
                self.bot.bl_wrapper = BusinessLayerWrapper(
                    mm_bl, pt_bl, vrc_bl, p_bl, web_bl, mod_bl
                )

                extensions = [name for name in self.bot.extensions.keys()]
                for m in extensions:
                    try:
                        await self.bot.reload_extension(m)
                    except Exception as e:
                        await ctx.send(f"Failed to reload `{module_name}`")
                        log.exception(f"Failed to reload {m.split('.')[-1]}")
                log.warning(
                    f"{ctx.author.display_name} reloaded ALL from #{ctx.channel.name}"
                )
                await ctx.send(f"Successfully reloaded ALL")
            else:
                module = f"layers.ui.discord_commands.{module_name}"
                try:
                    await self.bot.reload_extension(module)
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

    @checks.is_team_bot_channel()
    @checks.is_programming_team()
    @commands.command()
    async def tree(self, ctx: commands.Context):
        """
        One modification is enough to justify tree sync
        https://gist.github.com/AbstractUmbra/a9c188797ae194e592efe05fa129c57f
        """

        onlineList = await ctx.bot.tree.fetch_commands(
            guild=discord.Object(id=settings.SERVER_ID)
        )
        online = {ele.name: ele for ele in onlineList}
        currentList = ctx.bot.tree.get_commands(
            guild=discord.Object(id=settings.SERVER_ID)
        )
        current = {ele.name: ele for ele in currentList}
        addition = []
        deletion = []
        mod = []
        for konline in online:
            if konline not in current:
                deletion.append(konline)
            else:
                onlineCommand: discord.app_commands.AppCommand = online[konline]
                currentCommand = current[konline]
                if len(onlineCommand.options) != len(currentCommand.parameters):
                    mod.append(f"/{konline} parameter number changed")
                    continue
                if onlineCommand.description != currentCommand.description:
                    mod.append(f"/{konline} description changed")
                    continue
                for i in range(len(onlineCommand.options)):
                    ocmd = onlineCommand.options[i]
                    ccmd = currentCommand.parameters[i]
                    if (
                        ocmd.description != ccmd.description
                        or ocmd.name != ccmd.name
                        or ocmd.type != ccmd.type
                    ):
                        mod.append(f"/{konline} one parameter desc/name/type changed")
                        break
        for kcur in current:
            if kcur not in online:
                addition.append(kcur)

        await send_long(
            ctx.channel,
            f"add : {addition}\ndeletion:{deletion}\nmod:{mod}",
            mention=False,
        )
        text = "Apply tree modification?"
        if not (len(addition) or len(deletion) or len(mod)):
            text = (
                ":warning: no modification found :warning:\nYou do no need to sync the tree\n"
                + text
            )

        msgbox = Confirm(text)
        result = await msgbox.prompt(ctx)
        if not result:
            await ctx.send("Canceled")
            return

        await ctx.bot.tree.sync(guild=discord.Object(id=settings.SERVER_ID))
        await ctx.send("done")

async def setup(bot):
    await bot.add_cog(Programming(bot))
