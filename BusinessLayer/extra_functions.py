# Standard
from typing import Optional
import discord
from os import _exit
import traceback
import asyncio
from nest_asyncio import apply
from io import StringIO, BytesIO
from termcolor import colored
from datetime import datetime
from sys import stdout
import Settings

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


async def handle_error(bot, title, traceback_string):
    error_text = f"***ERROR***\n\n{title}\n{traceback_string}"
    ts_print(error_text)

    channel = bot.get_channel(Settings.ERROR_LOG_CHANNEL)
    await send_long(channel, error_text)


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


async def clean_shutdown(
    bot, location="the console", person="KeyboardInterrupt", exit=True
):
    """
    Cleanly shutdown the bot. Please specify ctx.channel.name as location,
    and ctx.author.display_name as person, assuming called from a Discord command.
    """

    # Log the shutdown
    msg_string = f"WARNING: Bot {'shut down' if exit else 'restarted'} from {location} by {person}"
    channel = bot.get_channel(Settings.ERROR_LOG_CHANNEL)
    await channel.send(msg_string)
    ts_print(msg_string)

    if exit:
        # Stop the event loop and exit Python. The OS should be
        # calling this script inside a loop if you want the bot to restart
        loop = asyncio.get_event_loop()
        loop.stop()
        _exit(0)


def ts_print(*objects, sep=" ", end="\n", file=stdout, flush=False):
    """Adds a colored timestamp to debugging messages in the console"""

    if len(objects) == 0 or (objects[0] == "" and len(objects) == 1):
        print("")
        return
    timestamp = colored(datetime.now().strftime("%b-%d-%Y %H:%M:%S"), "green") + " - "
    print(
        timestamp + str(objects[0]),
        *objects[1:],
        sep=sep,
        end=end,
        file=file,
        flush=flush,
    )
