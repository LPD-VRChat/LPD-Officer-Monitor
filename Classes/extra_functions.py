# Standard
import discord
from io import StringIO, BytesIO
from statistics import mode as mode
from Classes.menus import Confirm
from datetime import datetime
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

async def process_mugshot(ctx, bot):
    """
    Process a mugshot and identify what world it was in
    """
    
    try:
        voice_channel = ctx.message.author.voice.channel
    except:
        await ctx.channel.send("ERROR: You don't seem to be in a voice channel. Please be in a voice channel when posing a mugshot.", delete_after=15)
        return
        
    officer_id = ctx.message.author.id
    content = ctx.message.clean_content
    jump_url = ctx.message.jump_url
    
    world_list = []
    
    for user in voice_channel.members:
        request_string = f"SELECT world_name from VRChatActivity WHERE officer_id = {user.id} AND datetime = (SELECT MAX(datetime) FROM VRChatActivity WHERE officer_id = {user.id})"
            
        world_list.append(await bot.officer_manager.send_db_request(request_string, None))
        
    
    criminal_name_list = content.split('\n', 1)[0].split(' ')[1:]
    criminal_name = ' '.join(criminal_name_list)
    arrest_world = mode(world_list)[0][0]
    
    arresting_officers = ctx.message.mentions
    if ctx.message.author not in arresting_officers:
        arresting_officers = arresting_officers.append(ctx.message.author)
        
    crime_list = content.split('\n', 1)[1].split(' ')[1:]
    crime = ' '.join(crime_list)
    
    officers_involved = ''
    for mentioned in arresting_officers:
        officers_involved = f"{officers_involved}{mentioned.id},"
    
    
    
    error1 = ''
    error2 = ''
    error3 = ''
    
    result = await Confirm(f"It looks like you arrested `{criminal_name}` in `{arrest_world}` for `{crime}`... Is this correct?").prompt(ctx)
    
    if result:
        pass
    
    else:
    
        result2 = await Confirm("Was the criminal's name correct?").prompt(ctx)
        
        if result2:
            pass
        
        else:
            error1 = 'CRIMINAL_NAME_ERROR'
            await ctx.channel.send(f"Notifying the Programming Team about this bug: ERROR_TYPE: {error1}", delete_after=15)
            
        
        result3 = await Confirm("Was the world name correct?").prompt(ctx)
        
        if result3 and result2:
            pass
        
        else:
            error2 = 'WORLD_NAME_ERROR'
            await ctx.channel.send(f"Notifying the Programming Team about this bug: ERROR_TYPE: {error2}", delete_after=15)
    
        result4 = await Confirm("Was the crime correct?").prompt(ctx)
        
        if result2 and result3 and result4:
            pass
            
        else:
            error3 = 'CRIME_ERROR'
            await ctx.channel.send(f"Notifying the Programming Team about this bug: ERROR_TYPE: {error3}", delete_after=15)
    
    error = error1 + ', ' + error2 + ', ' + error3
    
    if error1 == '' and error2 == '' and error3 == '':
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        request_string = f"INSERT INTO Mugshots (officer_id, world_name, criminal_name, datetime, crime, officers_involved) VALUES ({officer_id}, '{arrest_world}', '{criminal_name}', '{now}', '{crime}', '{officers_involved}')"
        await ctx.channel.send("Okie Dokie. We'll save it.", delete_after=15)
        await bot.officer_manager.send_db_request(request_string, None)
    
    else:
        cap_destructo = bot.get_guild(bot.settings["Server_ID"]).get_member(
                249404332447891456
            )
        await cap_destructo.send(f"Hi Captain Destructo. Looks like there was an issue with processing a mugshot. Here's the jump_url: {jump_url}\n    ERROR: {error}\n    Processed world name: {arrest_world}\n    Processed criminal name: {criminal_name}\n    Processed crime: {crime}\n    Processed Officer IDs involved: {officers_involved}")
  
