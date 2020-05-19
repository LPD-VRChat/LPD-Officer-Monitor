# Standard
import traceback

# Community
import discord
from discord.ext import commands

# Mine
from Classes.extra_functions import handle_error


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.dark_green()
        self.missing_help_information_str = "No help information"

    def get_title(self, command):
        return f"{self.bot.command_prefix}{command.name} {command.signature}"

    def _get_short_long_description(self, long_help_text):
        # Make sure their is a long_help_text
        if not long_help_text:
            return (self.missing_help_information_str, self.missing_help_information_str)
        
        # Split the long_help_text
        split_help_text = long_help_text.split("\n")

        # Fill the short_desc and long_desc
        short_desc_done = False
        short_desc = ""
        long_desc = ""

        # Use the raw parser
        if split_help_text[-1] == "PARSE RAW":
            short_desc = split_help_text[0]
            long_desc = "\n".join(split_help_text[0:-2])
        # Use the more complicated parser I wrote
        else:
            for line in split_help_text:
                if not short_desc_done:
                    if line != "": short_desc += line
                    else: short_desc_done = True

                if line != "": long_desc += line + " "
                else: long_desc += "\n\n"
        
        # Return the data
        return (short_desc, long_desc)

    def get_short_description(self, long_help_text):
        return self._get_short_long_description(long_help_text)[0]

    def get_long_description(self, long_help_text):
        return self._get_short_long_description(long_help_text)[1]

    @staticmethod
    async def can_use(command, ctx):
        try:
            await command.can_run(ctx)
            return True
        except commands.CommandError: return False

    @staticmethod
    async def send_error(ctx, error_message):
        await ctx.send(None, embed=discord.Embed(
            title="Error",
            description=error_message,
            color=discord.Color.red()
        ))


    @commands.command(pass_context=True)
    @commands.has_permissions(add_reactions=True,embed_links=True)
    async def help(self, ctx, *command):
        """Get information about all the commands."""

        try:

            # This is if the user does just to help, and does not try to get information about a specific command
            if not command:
                
                # Create the embed
                all_help_embeds = [discord.Embed(
                    title="Accessable commands",
                    description=f"Use `{self.bot.command_prefix}help command` to get more information about a specific command.",
                    color=discord.Color.from_rgb(255, 255, 51)
                )]
                
                # Loop through all the commands and add them to the embed if they are available in the current context
                print(self.bot.cogs)
                for cog_name in self.bot.cogs:

                    cog = self.bot.cogs[cog_name]
                    try:
                        cog_embed = discord.Embed(
                            title=cog_name,
                            description=cog.description,
                            color=cog.color
                        )
                    except AttributeError:
                        cog_embed = discord.Embed(
                            title=cog_name,
                            description=cog.description
                        )

                    for single_command in cog.get_commands():
                        if await self.can_use(single_command, ctx):
                            title = self.get_title(single_command)
                            short_description = self.get_short_description(single_command.help)
                            cog_embed.add_field(name=title, value=short_description, inline=False)
                    
                    all_help_embeds.append(cog_embed)

                # Send the embed
                for embed in all_help_embeds:
                    await ctx.send(None, embed=embed)
            
            # The user is requesting more information about a command
            else:
                # This warns the user if he passed in too many arguments
                if len(command) > 1:
                    await self.send_error(ctx, "You passed in too many arguments.")
                    return# Exit the command
                
                # Give information about a specific command
                for command_in_bot in self.bot.commands:

                    # If the command is found
                    if command_in_bot.name == command[0]:

                        # Make sure the command can be used in the current context
                        if await self.can_use(command_in_bot, ctx):
                            await ctx.send(None, embed=discord.Embed(
                                title=self.get_title(command_in_bot),
                                description=self.get_long_description(command_in_bot.help),
                                color=discord.Color.green()
                            ))
                        else: await self.send_error(ctx, "The command you searched for cannot be used here.")
                        break

                # If the command was not found
                else: await self.send_error(ctx, "The command you searched for was not found.")

        except Exception as error:
            await ctx.send("Something failed with the help command.")
            await handle_error(self.bot, error, traceback.format_exc())