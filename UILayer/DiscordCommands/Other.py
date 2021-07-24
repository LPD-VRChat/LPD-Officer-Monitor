# Settings import
import Settings

# Standard
import traceback
import asyncio
import argparse
from typing import List, Set, Tuple, Dict

# Community
import discord
from discord.ext import commands
from fuzzywuzzy.process import extractBests

# Mine
from BusinessLayer.extra_functions import handle_error
from BusinessLayer.extra_functions import ts_print as print
import BusinessLayer.checks as checks
import BusinessLayer.errors as errors

from BusinessLayer.extra_functions import send_long


class Other(commands.Cog):
    def __init__(self, bot):
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
    @commands.command()
    async def rtv(self, ctx, *arguments):
        """This command searches server members, and returns a list of members having the role"""
        if arguments and "-i" not in arguments and "--include" not in arguments:
            if arguments[0] == "-x" or arguments[0] == "--exclude":
                role_names = [123]

            if arguments and "-x" not in arguments and "--exclude" not in arguments:
                excluded_role_names = None

        if ctx.message.clean_content.strip() == f"{Settings.BOT_PREFIX}rtv":
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

            parsed = parser.parse_args(arguments)

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
            results = set(self.bot.guild.members)
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


def setup(bot):
    bot.add_cog(Other(bot))
