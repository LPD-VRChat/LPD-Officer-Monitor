# Settings import
import settings

# Standard
import argparse
from typing import List, Set, Tuple

# Community
import discord
from discord.ext import commands
from fuzzywuzzy.process import extractBests

# Custom
import src.BusinessLayer.checks as checks
import src.BusinessLayer.errors as errors

from src.BusinessLayer.bl_wrapper import BusinessLayerWrapper
from src.BusinessLayer.extra_functions import send_long


class Other(commands.Cog):
    def __init__(self, bot):
        self.bl_wrapper: BusinessLayerWrapper = bot.bl_wrapper
        self.bot = bot
        self.color = discord.Color.green()

    @staticmethod
    def remove_name_decoration(name: str) -> str:
        """
        Remove the discord special characters at the start and end of the string
        """
        return name.strip("| ⠀ ")

    def get_role_by_name(self, role_name: str) -> discord.Role:
        """
        Returns a role object from a given name
        """
        role_names = []

        for role in self.bot.guild.roles:
            sanitized_name = self.remove_name_decoration(role.name)
            role_names.append(sanitized_name)
            if sanitized_name.lower() == role_name.lower():
                return role
        msg = f"The role `{role_name}` could not be found.\n Did you mean: `{', '.join(role_names)}`?"
        cutoff_score = 75
        suggestions: List[Tuple[str, int]] = []

        # usually you get something on the first run, sometimes if you write really badly you won't get anything
        # lower the score to get more suggestions
        while len(suggestions) < 1 and len(role_name) > 1 and cutoff_score > 0:
            suggestions = extractBests(role_name, role_names, score_cutoff=cutoff_score)
            # if only one suggestion, give result immediately instead of suggest and having to type cmd again
            if cutoff_score == 75 and len(suggestions) == 1:
                try:
                    return self.get_role_by_name(suggestions[0][0])
                except errors.GetRoleMembersError as e:
                    print(
                        f"ERROR: rtv, Could not find role `{suggestions[0][0]}`, msg:",
                        e,
                    )
                    pass  # if role not found, we use original name to find suggestions

            cutoff_score -= 25

        for suggest in suggestions:
            # it's better to include quotes for copy paste correct role
            if " " in suggest[0]:
                msg += f'  `"{suggest[0]}"`'
            else:
                msg += f"  `{suggest[0]}`"
        raise errors.GetRoleMembersError(message=msg)

    def get_role_members(self, role: discord.Role) -> List[discord.Member]:
        # Make sure that people have the role
        if not role.members:
            raise errors.GetRoleMembersError(message=f"`{role.name}` is empty.")

        # Sort the members
        return sorted(
            role.members, key=lambda m: self.remove_name_decoration(m.name).lower()
        )

    @checks.is_team_bot_channel()
    @commands.check_any(
        checks.is_dev_team(), checks.is_team_lead(), checks.is_white_shirt()
    )
    @commands.command(usage="discordRole | -i includedRole -x excludedRole")
    async def rtv(self, ctx, *arguments):
        """This command searches server members, and returns a list of members having the role"""
        if arguments and "-i" not in arguments and "--include" not in arguments:
            if arguments[0] == "-x" or arguments[0] == "--exclude":
                role_names = [123]

            if arguments and "-x" not in arguments and "--exclude" not in arguments:
                excluded_role_names = None

        if ctx.message.clean_content.strip() == f"{settings.BOT_PREFIX}rtv":
            raise errors.MissingArgumentError(message="Missing arguments.")

        if (
            "-i" not in arguments
            and "--include" not in arguments
            and "-x" not in arguments
            and "--exclude" not in arguments
        ):
            role_names = [" ".join(arguments)]
            excluded_role_names = None

        else:
            parser = argparse.ArgumentParser()
            parser.add_argument("-i", "--include", action="append")
            parser.add_argument("-x", "--exclude", action="append")

            try:
                parsed = parser.parse_args(arguments)
            except:
                await ctx.send(
                    "When searching for multiple roles, you must provide all roles as arguments."
                )
                return

            if parsed.include:
                role_names = parsed.include
            else:
                role_names = [123]

            if parsed.exclude:
                excluded_role_names = parsed.exclude
            else:
                excluded_role_names = None

        results: Set[discord.Member] = set()

        if role_names is None:
            raise errors.MissingArgumentError(
                message="You must specify a role to search for.",
                argument_name="role_name",
            )
            return

        if role_names == [123]:
            results = set(ctx.bot.guild.members)
            roles_search = None

        else:
            roles_search: List[discord.Role] = [
                self.get_role_by_name(role_name) for role_name in role_names
            ]
            for role in roles_search:
                if len(results) == 0:
                    results.update(self.get_role_members(role))
                else:
                    results = results.intersection(self.get_role_members(role))

        if excluded_role_names is not None:
            roles_excluded: List[discord.Role] = [
                self.get_role_by_name(role_name) for role_name in excluded_role_names
            ]
            for role in roles_excluded:
                results.difference_update(self.get_role_members(role))

        if not results:
            raise errors.MemberNotFoundError(
                message="No members were found with your specified criteria."
            )
            return

        # Sort the results by display_name
        member_names = sorted(results, key=lambda m: m.display_name.lower())
        member_str = "\n".join(member.name for member in member_names)
        role_or_roles = (
            "role" if role_names == [123] or len(roles_search) == 1 else "roles"
        )
        role_or_roles_x = (
            "role"
            if excluded_role_names is None or len(roles_excluded) == 1
            else "roles"
        )

        role_names_we_searched = (
            role_or_roles
            + " "
            + ", ".join(
                [
                    "`" + self.remove_name_decoration(role.name) + "`"
                    for role in roles_search
                ]
            )
            if roles_search
            else ""
        )

        await ctx.send(
            f"Here are the {len(member_names)} people with the {role_names_we_searched}"
            + f"{' and the ' if role_names != [123] and excluded_role_names else ''}{'excluded ' + role_or_roles_x + ' ' if excluded_role_names else ''}"
            + f"{', '.join(['`'+self.remove_name_decoration(role.name)+'`' for role in roles_excluded]) if excluded_role_names else ''}:"
        )
        await send_long(ctx.channel, member_str, code_block=True)

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command()
    async def count_officers(self, ctx):
        """
        This command returns an embed with a count of all officers by rank,
        as well as a total count.
        """

        all_lpd_members = self.get_role_members(
            ctx.bot.guild.get_role(settings.LPD_ROLE)
        )

        # For every rank in settings.ROLE_LADDER, get the number of members with the role having that rank.id
        # Then add that to a dictionary with the role name as the key, and the number of members as the value.

        # Create a dictionary of all the roles and their corresponding member count
        # This will be used to create the embed later.
        # The keys are the role names, and the values are the member count.

        all_officer_count = len(all_lpd_members)

        # Create an embed to send to the channel
        embed = discord.Embed(
            title="Number of all LPD Officers: " + str(all_officer_count),
            colour=discord.Colour.dark_green(),
        )

        for rank in settings.ROLE_LADDER.__dict__.values():
            role = ctx.bot.guild.get_role(rank.id)
            if role is None:
                continue

            rank_name = self.remove_name_decoration(role.name)
            if rank_name == "Cadet":
                rank_name = "LPD " + rank_name

            embed.add_field(
                name=rank_name,
                value="**"
                + str(len(self.get_role_members(role)))
                + "**"
                + " ("
                + str(
                    round(100 * len(self.get_role_members(role)) / all_officer_count, 2)
                )
                + "%)",
                inline=True,
            )

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Other(bot))
