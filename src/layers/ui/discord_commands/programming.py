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
import os

# Community
import discord
from discord.ext import commands

# Custom
import src.layers.business.checks as checks
import src.layers.business.bl_wrapper as bl_wrapper
from src.layers.business.extra_functions import send_long, msgbox_confirm
from src.layers import business as bl


log = logging.getLogger("lpd-officer-monitor")


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
            "#" + ctx.channel.name,
            ctx.author.display_name,
            exit_code=0,
        )

    @checks.is_team_bot_channel()
    @checks.is_programming_team()
    @commands.command()
    async def restart(self, ctx):
        """Restarts the bot if something is broken"""
        if not os.environ.get("LPD_OFFICER_MONITOR_DOCKER"):
            await ctx.send("Unable to restart outside a container")
            return
        await ctx.send("Restarting the bot...")
        await self.bl_wrapper.p.clean_shutdown(
            "#" + ctx.channel.name,
            ctx.author.display_name,
            exit_code=75,  # EX_TEMPFAIL
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
            self.bot.bl_wrapper: bl_wrapper.BusinessLayerWrapper = self.bl_wrapper

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

                # self.bot.dispatch("shutdown")
                # this creates a task that get's wiped because of exit or loop stop
                for event in self.bot.extra_events.get("on_unload", []):
                    # WARNING: `extra_events` accessing none documented public variable !!!
                    try:
                        await discord.utils.maybe_coroutine(event)
                    except:
                        log.exception("Failed to call `on_unload`")
                try:
                    for name, module in loadedModules.items():
                        if name.startswith("src.layers.business"):
                            importlib.reload(module)
                except Exception as e:
                    await ctx.send(f"Failed to reload business layer")
                    log.exception(f"Failed to reload business layer")
                    return

                bl_wrapper.destroy(self.bot.bl_wrapper)
                self.bot.bl_wrapper = bl_wrapper.create(self.bot)

                extensions = [name for name in self.bot.extensions.keys()]
                for m in extensions:
                    try:
                        await self.bot.reload_extension(m)
                    except Exception as e:
                        await ctx.send(f"Failed to reload `{module_name}`")
                        log.exception(f"Failed to reload {m.split('.')[-1]}")
                self.bot.has_been_started = False
                self.bot.dispatch("connect")
                self.bot.dispatch("ready")
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
    @commands.command(aliases=["tree"])
    async def slash_sync(self, ctx: commands.Context):
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

        msgbox_confirm
        if not await msgbox_confirm(ctx, text):
            return

        await ctx.bot.tree.sync(guild=discord.Object(id=settings.SERVER_ID))
        await ctx.send(content="Command tree synced sucessfully!", view=None)

    @checks.is_team_bot_channel()
    @checks.is_programming_team()
    @commands.command()
    async def slash_req(self, ctx: commands.Context):
        embeds = []
        for cog_name in ctx.bot.cogs:
            cog_embed = discord.Embed(
                title=cog_name,
                description=ctx.bot.cogs[cog_name].description,
                color=getattr(ctx.bot.cogs[cog_name], "color", discord.Color.purple()),
            )
            for cmd in ctx.bot.cogs[cog_name].walk_app_commands():
                if isinstance(cmd, discord.app_commands.Group):
                    logging.error("Groups is not handled")  # TODO
                    continue
                checks_txt = ""
                for check in cmd.checks:
                    checks_txt += f"`{check.__qualname__.split('.<locals>')[0]}`\n"
                if len(checks_txt):
                    cog_embed.add_field(name="/" + cmd.name, value=checks_txt)
            for tcmd in ctx.bot.cogs[cog_name].walk_commands():
                if isinstance(tcmd, commands.Group):
                    logging.error("Groups are not handled")  # TODO
                    continue
                if not isinstance(tcmd, commands.HybridCommand):
                    continue
                checks_txt = ""
                for check in tcmd.checks:
                    checks_txt += f"`{check.__qualname__.split('.<locals>')[0]}`\n"
                if len(checks_txt):
                    cog_embed.add_field(name="/" + tcmd.name, value=checks_txt)
            if len(cog_embed.fields):
                embeds.append(cog_embed)

        while len(embeds) > 0:
            await ctx.send(None, embeds=embeds[0:10])
            embeds = embeds[10:]


async def setup(bot):
    await bot.add_cog(Programming(bot))
