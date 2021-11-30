# Standard
from typing import Optional
import discord
from nest_asyncio import apply
from io import StringIO, BytesIO
from datetime import datetime
from sys import stdout
import settings

apply()


async def send_long(channel, string, code_block=False, mention=True):
    """Send output as a text file, or optionally a code block if code_block=True is passed"""

    # Set allowed mentions
    allowed_mentions = (
        discord.AllowedMentions.all() if mention else discord.AllowedMentions.none()
    )

    # Make a function to check the length of all the lines
    str_list_len = lambda str_list: sum(len(i) + 1 for i in str_list)

    # Add a code block around the string if needed.
    if code_block:
        input_string_list = ("```\n" + string + "\n```").splitlines()
    else:
        input_string_list = string.splitlines()

    output_list = []
    for line in input_string_list:

        # If the line is longer that 2000, send it as a file and exit.
        if len(line) > 2000:
            await send_str_as_file(
                channel=channel,
                file_data=string,
                filename="long_output.txt",
                msg_content="The output is too big to fit in a discord message so it is insted in a file.",
            )
            return

        # Calculate the output length
        #            Previous output            \n   this line   the backticks if that is enabled
        output_len = (
            str_list_len(output_list)
            + 1
            + len(line)
            + (len("```") if code_block else 0)
        )

        # Check the output length
        if output_len < 2000:
            output_list.append(line)
        else:
            # Send the full message and add backticks if needed
            await channel.send(
                "\n".join(output_list) + ("```" if code_block else ""),
                allowed_mentions=allowed_mentions,
            )
            # Add the backticks if the message should be in a codeblock
            output_list = [("```" if code_block else "") + line]

    await channel.send("\n".join(output_list), allowed_mentions=allowed_mentions)


async def send_str_as_file(
    channel: discord.TextChannel,
    file_data: str,
    filename: Optional[str] = None,
    msg_content: Optional[str] = None,
) -> None:
    with BytesIO(file_data.encode("utf8")) as error_file:
        await channel.send(
            msg_content, file=discord.File(error_file, filename=filename)
        )


def has_role_id(member: discord.Member, role_id: int) -> bool:
    """Returns true if the member has the given role"""
    return role_id in [r.id for r in member.roles]


def is_lpd_member(member: discord.Member):
    """
    Returns if a member is an LPD member based on their discord roles.
    """
    lpd_role_set = {v.id for k, v in settings.ROLE_LADDER.items()}
    member_rank_roles = set(member.roles).intersection(lpd_role_set)
    return len(member_rank_roles) != 0


def lpd_rank(member: discord.Member):
    pass