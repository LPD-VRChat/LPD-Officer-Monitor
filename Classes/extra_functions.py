# Standard
import discord
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
    str_list_len = lambda str_list: sum(len(i)+1 for i in str_list)

    output_list = []
    for line in string.splitlines():
        
        # Calculate the output length
        #            Previous output            \n   this line   the backticks is that is enabled
        output_len = str_list_len(output_list) + 1 + len(line) + (len("```") if code_block else 0)

        # Check the output length
        if output_len < 2000: output_list.append(line)
        else:
            # Send the full message and add backticks if needed
            await channel.send("\n".join(output_list) + ("```" if code_block else ""))
            # Add the backticks if the message should be in a codeblock
            output_list = [("```" if code_block else "") + line]
            
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
    await send_long(channel, error_text)

def get_rank_id(settings, name_id):
    role_ladder = settings["role_ladder"]

    for role in role_ladder:
        if role["name_id"] == name_id:
            return role["id"]
    
    return None

def has_role(role_list, role_id):
    return len([x for x in role_list if x.id == role_id]) > 0