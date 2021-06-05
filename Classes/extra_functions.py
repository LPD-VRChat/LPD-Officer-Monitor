# Standard
from typing import Optional
import discord
from os import _exit
import asyncio
from io import StringIO, BytesIO
from termcolor import colored
from datetime import datetime

# Community
import commentjson as json


def is_number(string):
    try:
        int(string)
        return True
    except ValueError:
        return False


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



async def clean_shutdown(bot, location="the console", person="KeyboardInterrupt", exit=True):
    """
    Cleanly shutdown the bot. Please specify ctx.channel.name as location,
    and ctx.author.display_name as person, assuming called from a Discord command.
    """

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
    msg_string = f"WARNING: Bot {'shut down' if exit else 'restarted'} from {location} by {person}"
    channel = bot.get_channel(bot.settings["error_log_channel"])
    await channel.send(msg_string)
    print(msg_string)

    if exit:
        # Stop the event loop and exit Python. The OS should be
        # calling this script inside a loop if you want the bot to restart
        loop = asyncio.get_event_loop()
        loop.stop()
        _exit(0)


async def analyze_promotion_request(bot, message, timeout_in_seconds=7200):
    """This function analyzes a message to determine eleigbility for promotion, and automatically apply the promotion when reactions are received."""

    officer = bot.officer_manager.get_officer(message.author.id)

    if (
        "trained by" not in message.content.lower()
        or "request rank" not in message.content.lower()
        or not officer
        or len(message.mentions) == 0
    ):
        return

    # fmt: off
    cadet_role = bot.officer_manager.guild.get_role(get_rank_id(bot.settings, "cadet"))
    recruit_role = bot.officer_manager.guild.get_role(get_rank_id(bot.settings, "recruit"))
    officer_role = bot.officer_manager.guild.get_role(get_rank_id(bot.settings, "officer"))
    senior_officer_role = bot.officer_manager.guild.get_role(get_rank_id(bot.settings, "senior_officer"))
    corporal_role = bot.officer_manager.guild.get_role(get_rank_id(bot.settings, "corporal"))

    trainer_role = bot.officer_manager.guild.get_role(bot.settings["trainer_role"])
    lmt_trainer_role = bot.officer_manager.guild.get_role(bot.settings["lmt_trainer_role"])
    slrt_trainer_role = bot.officer_manager.guild.get_role(bot.settings["slrt_trainer_role"])
    prison_trainer_role = bot.officer_manager.guild.get_role(bot.settings["prison_trainer_role"])

    lmt_trained_role = bot.officer_manager.guild.get_role(bot.settings["lmt_trained_role"])
    slrt_trained_role = bot.officer_manager.guild.get_role(bot.settings["slrt_trained_role"])
    watch_officer_role = bot.officer_manager.guild.get_role(bot.settings["watch_officer_role"])
    # fmt: on

    requestables = {
        "recruit": {
            "name": "Recruit",
            "name_id": "recruit",
            "role": recruit_role,
            "prereq": cadet_role,
            "approver": trainer_role,
            "failmessage": "You must have the LPD Cadet role before you can request promotion to Officer. Please contact a White Shirt if you feel this message is in error.",
            "upgrade": True,
        },
        "senior officer": {
            "name": "Senior Officer",
            "name_id": "senior_officer",
            "role": senior_officer_role,
            "prereq": officer_role,
            "approver": trainer_role,
            "failmessage": "You must have the LPD Officer role before you can request promotion to Senior Officer. Please contact a White Shirt if you feel this message is in error.",
            "upgrade": True,
        },
        "slrt": {
            "name": "SLRT",
            "name_id": "slrt",
            "role": slrt_trained_role,
            "prereq": senior_officer_role,
            "approver": slrt_trainer_role,
            "failmessage": "You must have the LPD Senior Officer rank or higher before you can request assignment to the SLRT team. Please contact a White Shirt if you feel this message is in error.",
            "upgrade": False,
        },
        "watch officer": {
            "name": "Watch Officer",
            "name_id": "watch_officer",
            "role": watch_officer_role,
            "prereq": corporal_role,
            "approver": prison_trainer_role,
            "failmessage": "You must have the LPD Corporal rank or higher before you can request assignment to the Watch Officer team. Please contact a White Shirt if you feel this message is in error.",
            "upgrade": False,
        },
        "lmt": {
           "name": "LMT",
           "name_id": "lmt",
           "role": lmt_trained_role,
           "prereq": officer_role,
           "approver": lmt_trainer_role,
           "failmessage": "You must have the LPD Officer rank or higher before you can request assignment to the LMT team. Please contact a White Shirt if you feel this message is in error.",
           "upgrade": False,
        },
    }

    def get_approvers(role):
        _valid_approvers = []
        for member in message.mentions:
            if role in member.roles:
                _valid_approvers.append(member.id)
        return _valid_approvers

    def check(reaction, user, valid_approvers):
        if (
            user.id in valid_approvers
            and reaction.emoji == "\N{WHITE HEAVY CHECK MARK}"
        ):
            valid_approvers.remove(user.id)
            return reaction, user

    for key in requestables.keys():
        if key in message.content.lower():

            # React with a white checkmark to give the trainers something to click
            await message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

            # If prerequisite not met, delete message and notify user
            if (
                requestables[key]["upgrade"]
                and officer.rank != requestables[key]["prereq"]
            ) or (
                not requestables[key]["upgrade"]
                and officer.rank.position < requestables[key]["prereq"].position
            ):
                await message.delete()
                await message.channel.send(
                    requestables[key]["failmessage"], delete_after=10
                )
                return

            # Code to watch for approving checks
            valid_approvers = get_approvers(requestables[key]["approver"])
            try:
                reaction, user = await bot.wait_for(
                    "reaction_add",
                    timeout=timeout_in_seconds,
                    check=lambda reaction, user: check(reaction, user, valid_approvers),
                )

                if requestables[key]["upgrade"]:
                    await officer.promote()
                else:
                    await message.author.add_roles(requestables[key]["role"])

            except asyncio.TimeoutError:
                await message.remove_reaction("\N{WHITE HEAVY CHECK MARK}", bot.user)

            # Only process one matching result from the for loop - nobody should be requesting multiple ranks at once
            return

    # If we haven't returned by now, it means that we have no clue what the user sent. For the sake of forward compatibility,
    # we aren't going to delete unknown messages. Just react with a question mark.
    await message.add_reaction("\N{BLACK QUESTION MARK ORNAMENT}")