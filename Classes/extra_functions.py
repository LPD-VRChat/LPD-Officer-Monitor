# Standard
from typing import Optional
import discord
from os import _exit as exit
from asyncio import get_event_loop
from nest_asyncio import apply
from io import StringIO, BytesIO

# Community
import commentjson as json

apply()


def is_number(string):
    try:
        int(string)
        return True
    except ValueError:
        return False


async def send_long(channel, string, code_block=False):
    """Send output as a text file, or optionally a code block if code_block=True is passed"""

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
            await channel.send("\n".join(output_list) + ("```" if code_block else ""))
            # Add the backticks if the message should be in a codeblock
            output_list = [("```" if code_block else "") + line]

    await channel.send("\n".join(output_list))


def get_settings_file(settings_file_name, in_settings_folder=True):

    # Add the stuff to the settings_file_name to make it link to the right file
    file_name = settings_file_name + ".json"

    # Add the settings folder to the filename if necessary
    if in_settings_folder:
        file_name = "settings/" + file_name

    # Get all the data out of the JSON file, parse it and return it
    with open(file_name, "r") as json_file:
        data = json.load(json_file)
    return data


async def handle_error(bot, title, traceback_string):
    error_text = f"***ERROR***\n\n{title}\n{traceback_string}"
    print(error_text)

    channel = bot.get_channel(bot.settings["error_log_channel"])
    await send_long(channel, error_text)


def get_rank_id(settings, name_id):
    """Returns the Discord Role ID for specified name_id"""

    role_ladder = settings["role_ladder"]

    for role in role_ladder:
        if role["name_id"] == name_id:
            return role["id"]

    return None


def has_role(role_list, role_id):
    return len([x for x in role_list if x.id == role_id]) > 0


def role_id_index(settings):
    """Process the role_ladder into a usable list when called"""

    role_id_ladder = []
    for entry in settings["role_ladder"]:
        role_id_ladder.append(entry["id"])
    return role_id_ladder


def get_role_name_by_id(settings, bad_role):
    """Identify a role's expected name by its ID"""

    for entry in settings["role_ladder"]:
        if entry["id"] == bad_role:
            return entry["name"]


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


def member_role_dict(member, verbose=False):
    """Generates a dictionary of roles"""

    role_dict = {}

    for role in member.roles:
        if role.is_default:
            continue
        if role.is_bot_managed:
            continue
        if role.is_integration:
            continue
        role_details = {}
        role_details["name"] = role.name
        role_details["color"] = role.color
        if role.is_premium_subscriber:
            role_details["is_premium_subscriber"] = True

        role_dict[role.id] = role_details if verbose else True

    return role_dict


async def clean_shutdown(bot, location="the console", person="KeyboardInterrupt"):
    """Cleanly shutdown the bot"""

    # Put all on-duty officers off duty - don't worry,
    # they'll be put back on duty next startup
    if bot.officer_manager is not None:
        print("")
        for officer in bot.officer_manager.all_officers.values():
            if officer.is_on_duty:
                await officer.go_off_duty()
        bot.officer_manager.loa_loop.stop()
        bot.officer_manager.loop.stop()
    else:
        print("Couldn't find the OfficerManager...")
        print("Stopping the bot without stopping time...")

    # Log the shutdown
    msg_string = f"WARNING: Bot shut down from {location} by {person}"
    channel = bot.get_channel(bot.settings["error_log_channel"])
    await channel.send(msg_string)
    print(msg_string)

    # Stop the event loop and exit Python. The OS should be
    # calling this script inside a loop if you want the bot to restart
    loop = get_event_loop()
    loop.stop()
    exit(0)
