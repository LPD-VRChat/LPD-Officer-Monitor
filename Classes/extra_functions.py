# Standard
import discord
from io import StringIO
from io import BytesIO

# Community
import commentjson as json


def is_number(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

async def send_long(channel, string):
    str_list_len = lambda str_list: sum(len(i)+1 for i in str_list)

    output_list = []
    for line in string.splitlines():
        if str_list_len(output_list) + len(line) + 1 < 2000:
            output_list.append(line)
        else:
            await channel.send("\n".join(output_list))
            output_list = [line]
    await channel.send("\n".join(output_list))

def get_settings_file(settings_file_name, in_settings_folder = True):
    
    # Add the stuff to the settings_file_name to make it link to the right file
    file_name = settings_file_name+".json"

    # Add the settings folder to the filename if necessary
    if in_settings_folder: file_name = "settings/" + file_name

    # Get all the data out of the JSON file, parse it and return it
    with open(file_name, "r") as json_file:
        data = json.load(json_file)
    return data

async def handle_error(bot, title, traceback_string):
    error_text = f"***ERROR***\n\n{title}\n{traceback_string}"
    print(error_text)

    channel = bot.get_channel(bot.settings["error_log_channel"])
    if len(error_text) < 2000:
        await channel.send(error_text)
    else:
        error_file_sio = StringIO(error_text)
        error_file = BytesIO(error_file_sio.read().encode('utf8'))

        await channel.send("The error output is too big to fit in a discord message so it is insted in a file.", file=discord.File(error_file, filename="Error.txt"))

        # with open("temp_file.txt", "w") as error_file:
        #     temp_file.write(error_text)
        # with open("temp_file.txt", "w") as error_file: