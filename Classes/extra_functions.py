# Standard
import discord
import datetime

from Classes.Officer import Officer.save_loa as save_loa
from io import StringIO, BytesIO

# Community
import commentjson as json


def is_number(string):
    try:
        int(string)
        return True
    except ValueError:
        return False


async def send_long(channel, string, code_block=False):

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
            with StringIO(string) as error_file_sio:
                with BytesIO(error_file_sio.read().encode("utf8")) as error_file:
                    await channel.send(
                        "The output is too big to fit in a discord message so it is insted in a file.",
                        file=discord.File(error_file, filename="long_output.txt"),
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

async def process_loa(message):

    # Try and parse the message to get a useful date range
    officer_id = message.author.id
    try:
        date_range = message.content.split(":")[0]
        date_a = date_range.split("-")[0]
        date_b = date_range.split("-")[1]
        date_start = ["", "", ""]
        date_end = ["", "", ""]
        date_start[0] = date_a.split("/")[0].strip()
        date_start[1] = date_a.split("/")[1].strip()
        date_start[2] = date_a.split("/")[2].strip()
        date_end[0] = date_b.split("/")[0].strip()
        date_end[1] = date_b.split("/")[1].strip()
        date_end[2] = date_b.split("/")[2].strip()
        reason = message.content.split(":")[1].strip()
        months = dict(
            JAN=1,
            FEB=2,
            MAR=3,
            APR=4,
            MAY=5,
            JUN=6,
            JUL=7,
            AUG=8,
            SEP=9,
            OCT=10,
            NOV=11,
            DEC=12,
        )
        int(date_start[0])
        int(date_end[0])
        
        if type(date_start[1]) != 'str':
            int(date_start[1])
        else:
            date_start[1] = date_start[1].upper()[0:3]
            date_start[1] = months[date_start[1]]

        if type(date_end[1]) != 'str':
            int(date_end[1])
        else:
            date_end[1] = date_end[1].upper()[0:3]
            date_end[1] = months[date_end[1]]
  
    except (TypeError, ValueError, KeyError, IndexError):
        # If all of that failed, let the user know with an autodeleting message
        await message.channel.send(
            message.author.mention
            + " Please use correct formatting: 21/July/2020 - 21/August/2020: Reason.",
            delete_after=10,
            )
        await message.delete()
        return

    
    date_start = [int(i) for i in date_start]
    date_end = [int(i) for i in date_end]

    if date_start[1] < 1 or date_start[1] > 12 or date_end[1] < 1 or date_end[1] > 12:
        # If the month isn't 1-12, let the user know they dumb
        await message.channel.send(
            message.author.mention + " There are only 12 months in a year.",
            delete_after=10,
        )
        await message.delete()
        return

    # Convert our separate data into a usable datetime
    date_start_complex = (
        str(date_start[0]) + "/" + str(date_start[1]) + "/" + str(date_start[2])
    )
    date_end_complex = (
        str(date_end[0]) + "/" + str(date_end[1]) + "/" + str(date_end[2])
    )
    date_start = datetime.datetime.strptime(date_start_complex, "%d/%m/%Y")
    date_end = datetime.datetime.strptime(date_end_complex, "%d/%m/%Y")

    if date_end > date_start + datetime.timedelta(
        weeks=+12
    ) or date_end < date_start + datetime.timedelta(weeks=+4):
        # If more than 12 week LOA, inform user
        await message.channel.send(
            message.author.mention
            + " Leaves of Absence are limited to 4-12 weeks. For longer times, please contact a White Shirt (Lieutenant or Above).",
            delete_after=10,
        )
        await message.delete()
        return

    # Fire the script to save the entry
    request_id = message.id
    await save_loa(bot, officer_id, date_start, date_end, reason, request_id)
    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')

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
    role_ladder = settings["role_ladder"]

    for role in role_ladder:
        if role["name_id"] == name_id:
            return role["id"]

    return None


def has_role(role_list, role_id):
    return len([x for x in role_list if x.id == role_id]) > 0


def role_id_index(settings):
    """
    Process the role_ladder into a usable list when called
    """
    role_id_ladder = []
    for entry in settings["role_ladder"]:
        role_id_ladder.append(entry["id"])
    return role_id_ladder

def get_role_name_by_id(settings, bad_role):
    """
    Identify a role's expected name by its ID
    """
    for entry in settings["role_ladder"]:
        if entry["id"] == bad_role:
            return entry["name"]
