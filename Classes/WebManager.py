import asyncio
import nest_asyncio

nest_asyncio.apply()

import time
from datetime import datetime, timedelta
import re
import signal
import moviepy.editor as mp
import numpy as np
from array2gif import write_gif
from urllib.parse import unquote_plus as dec
from os import path
from collections import OrderedDict
import json

from quart import Quart, redirect, url_for, request, send_file, render_template
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
from hypercorn.asyncio import serve
from hypercorn.config import Config

from Classes.extra_functions import role_id_index as _role_id_index
from Classes.extra_functions import geturls

app = Quart("LPD Officer Monitor")


async def _403_(missing_role=None):
    return await render_template("403.html.jinja", missing_role=missing_role)

def render_array(officer, filename=None, w=8, h=8):

    if filename == None:
        real_filename = "/tmp/APITextemp.gif"
    else:
        real_filename = filename

    _white_value_RGB = np.array([255, 255, 255])
    _black_value_RGB = np.array([0, 0, 0])
    _red_value_RGB = np.array([255, 0, 0])
    _green_value_RGB = np.array([0, 255, 0])
    _blue_value_RGB = np.array([0, 0, 255])
    _yellow_value_RGB = np.array([255, 255, 0])
    _cyan_value_RGB = np.array([0, 255, 255])
    _magenta_value_RGB = np.array([255, 0, 255])

    # This creates an array of arbitrary size based on the WxH size received on initialization.

    i = 0
    j = 0
    _base_row = []
    _base_array = []

    while j in range(0, w):
        _base_row.append(_black_value_RGB)
        j += 1

    while i in range(0, h):
        _base_array.append(_base_row)
        i += 1

    dataset = np.array(_base_array)

    z = w - 1

    dataset[0][z] = _white_value_RGB

    # In this section, we take the input dictionary and break it down into each value.
    # For adding bits, keep in mind that Udon starts at the bottom left, while python
    # starts at the top left.
    #
    # If you want to add values, do so here. Black is true White is false

    if officer == None:
        write_gif(dataset, real_filename)
        return

    dataset[0][0] = _white_value_RGB if officer.is_cadet else _black_value_RGB
    dataset[0][1] = _white_value_RGB if officer.is_white_shirt else _black_value_RGB
    dataset[0][
        2
    ] = (
        _white_value_RGB
    )  # Since we return the blank template if not officer, then we return true here always
    dataset[0][3] = _white_value_RGB if officer.is_moderator else _black_value_RGB
    dataset[0][4] = _black_value_RGB
    dataset[0][5] = _black_value_RGB
    dataset[0][6] = _black_value_RGB
    dataset[0][7] = _black_value_RGB

    dataset[1][0] = _white_value_RGB if officer.is_slrt_trained else _black_value_RGB
    dataset[1][1] = _white_value_RGB if officer.is_slrt_trainer else _black_value_RGB
    dataset[1][2] = _white_value_RGB if officer.is_lmt_trained else _black_value_RGB
    dataset[1][3] = _white_value_RGB if officer.is_lmt_trainer else _black_value_RGB
    dataset[1][4] = _black_value_RGB
    dataset[1][5] = _black_value_RGB
    dataset[1][6] = _black_value_RGB
    dataset[1][7] = _black_value_RGB

    dataset[2][0] = _white_value_RGB if officer.is_watch_officer else _black_value_RGB
    dataset[2][1] = _white_value_RGB if officer.is_prison_trainer else _black_value_RGB
    dataset[2][2] = _white_value_RGB if officer.is_instigator else _black_value_RGB
    dataset[2][3] = _white_value_RGB if officer.is_trainer else _black_value_RGB
    dataset[2][4] = _black_value_RGB
    dataset[2][5] = _black_value_RGB
    dataset[2][6] = _black_value_RGB
    dataset[2][7] = _black_value_RGB

    dataset[3][0] = _white_value_RGB if officer.is_chat_moderator else _black_value_RGB
    dataset[3][1] = _white_value_RGB if officer.is_event_host else _black_value_RGB
    dataset[3][2] = _white_value_RGB if officer.is_dev_member else _black_value_RGB
    dataset[3][3] = (
        _white_value_RGB if officer.is_media_production else _black_value_RGB
    )
    dataset[3][4] = _black_value_RGB
    dataset[3][5] = _black_value_RGB
    dataset[3][6] = _black_value_RGB
    dataset[3][7] = _black_value_RGB

    dataset[4][0] = _white_value_RGB if officer.is_janitor else _black_value_RGB
    dataset[4][1] = _white_value_RGB if officer.is_korean else _black_value_RGB
    dataset[4][2] = _white_value_RGB if officer.is_chinese else _black_value_RGB
    dataset[4][3] = _white_value_RGB if officer.is_inactive else _black_value_RGB
    dataset[4][4] = _black_value_RGB
    dataset[4][5] = _black_value_RGB
    dataset[4][6] = _black_value_RGB
    dataset[4][7] = _black_value_RGB

    dataset[5][0] = (
        _white_value_RGB if officer.is_programming_team else _black_value_RGB
    )
    dataset[5][1] = _black_value_RGB
    dataset[5][2] = _black_value_RGB
    dataset[5][3] = _black_value_RGB
    dataset[5][4] = _black_value_RGB
    dataset[5][5] = _black_value_RGB
    dataset[5][6] = _black_value_RGB
    dataset[5][7] = _black_value_RGB

    dataset[6][0] = _black_value_RGB
    dataset[6][1] = _black_value_RGB
    dataset[6][2] = _black_value_RGB
    dataset[6][3] = _black_value_RGB
    dataset[6][4] = _black_value_RGB
    dataset[6][5] = _black_value_RGB
    dataset[6][6] = _black_value_RGB
    dataset[6][7] = _black_value_RGB

    dataset[7][
        0
    ] = (
        _red_value_RGB
    )  ############### WARNING: We can't reliably check this value in an 8x8
    dataset[7][1] = _black_value_RGB
    dataset[7][2] = _black_value_RGB
    dataset[7][3] = _black_value_RGB
    dataset[7][4] = _black_value_RGB
    dataset[7][5] = _black_value_RGB
    dataset[7][6] = _black_value_RGB
    dataset[7][7] = _black_value_RGB

    # Save the GIF
    write_gif(dataset, real_filename)


# This is the documentation for the LPD Officer Monitor's VRChatVideoPlayer integration.

# In order to gather permissions for a VRChat user, VRChat must first send a request
# for a video file, with the username in the url parameters.

# This bot then grabs the officer object for that user, and this module processes the permissions
# for the user into a usable single frame GIF with minimum size 8x8.

# The bot then converts the GIF to a webm, which is returned to the video player. The Udon
# code then interprets that frame to get the RGB color values of the image.

# Currently this is just a binary system, with each pixel having a value of _black_value_RGB
# for False, and _white_value_RGB for True. Functionality will later be added for multi-state
# values, utilizing other colors.


class WebManager:
    def __init__(self, bot, app, config, loop):

        self.bot = bot
        self.app = app
        self.config = config
        self.loop = loop
        self.shutdown_event = asyncio.Event()
        self.__stop_the_server__ = False

    @classmethod
    async def configure(
        cls,
        _Bot,
        host="0.0.0.0",
        port=443,
        id=None,
        secret=None,
        token=None,
        callback=None,
        certfile=None,
        keyfile=None,
        _run_insecure=False,
    ):

        app.secret_key = b"random bytes representing quart secret key"

        app.config["DISCORD_CLIENT_ID"] = id  # Discord client ID.
        app.config["DISCORD_CLIENT_SECRET"] = secret  # Discord client secret.
        app.config["DISCORD_REDIRECT_URI"] = callback  # URL to your callback endpoint.
        app.config["DISCORD_BOT_TOKEN"] = token  # Required to access BOT resources.
        app.config["SERVER_NAMES"] = ["devbox.lolipd.com", "www.lolipd.com"]
        app.config["SCOPES"] = ["identify"]
        app.config["BOT"] = _Bot
        app.config["TEMPLATES_AUTO_RELOAD"] = True

        _Discord = DiscordOAuth2Session(app)
        app.config["DISCORD"] = _Discord

        if path.exists(certfile) and path.exists(keyfile) and not _run_insecure:
            _run_secure = True
        else:
            _run_secure = False

        config = Config()

        if _run_secure:
            config.certfile = certfile
            config.keyfile = keyfile
        else:
            port = 80

        config.bind = [f"{host}:{port}"]
        config.worker_class = ["asyncio"]
        config.server_names = ["devbox.lolipd.com", "www.lolipd.com"]
        config.accesslog = "/var/log/LPD-Officer-Monitor/access.log"
        config.errorlog = "/var/log/LPD-Officer-Monitor/error.log"

        loop = asyncio.get_event_loop()

        instance = cls(_Bot, app, config, loop)
        return instance

    async def shutdown_trigger(self):
        await asyncio.sleep(1)
        if self.__stop_the_server__:
            self.__stop_the_server__ = False
            return
        await self.shutdown_trigger()

    async def start(self):
        self.task = self.loop.create_task(
            serve(self.app, self.config, shutdown_trigger=self.shutdown_trigger)
        )

    def stop(self):
        self.__stop_the_server__ = True

    async def restart(self, wait_time=5):
        self.stop()
        await asyncio.sleep(wait_time)
        await self.start()

    async def reload(self):
        pass

    @app.route("/login/")
    async def login():
        discord = app.config["DISCORD"]
        return await discord.create_session(scope=app.config["SCOPES"])

    @app.route("/callback/")
    async def _callback():
        discord = app.config["DISCORD"]
        try:
            await discord.callback()
        except:
            pass
        return redirect(url_for(".home"))

    @app.errorhandler(Unauthorized)
    async def redirect_unauthorized(e):
        return redirect(url_for("login"))

    @app.route("/favicon.ico")
    async def favicon():
        return await send_file("/favicon.ico")

    @app.route("/")
    async def home():
        return await render_template("home.html.jinja", title="Welcome to the LPD!")

    @app.route("/officers", methods=["POST", "GET"])
    @requires_authorization
    async def display_officers():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        title = "Roster"
        time_results = None
        specified_officer = None
        _no_activity = False
        user = await discord.fetch_user()

        if request.method == "POST":
            officer = bot.officer_manager.get_officer(user.id)

            data = await request.form
            officer_id = int(data["officer_id"])
            specified_officer = bot.officer_manager.get_officer(officer_id)

            if specified_officer is not None and officer.is_white_shirt:
                result = await specified_officer.get_all_activity(
                    bot.officer_manager.all_monitored_channels
                )
                time_results = sorted(
                    result,
                    key=lambda x: time.mktime(x["time"].timetuple()),
                    reverse=True,
                )

                for result in time_results:
                    if result["channel_id"] is not None:
                        result["other_activity"] = bot.get_channel(
                            result["channel_id"]
                        ).name

                title = "Last Activity"

                if time_results == None:
                    _no_activity = True

            elif specified_officer is not None and not officer.is_white_shirt:
                title = "LPD Moderators only"

            else:
                title = "No such officer"

            if _no_activity and time_results is None:
                title = "No activity"
                time_results = [{"channel_id": "No activity", "other_activity": "None"}]

        role_list = []
        if bot.officer_manager.get_officer(user.id).is_white_shirt:
            role_ids = _role_id_index(bot.settings)
            all_officers = []
            guild = bot.officer_manager.guild
            for member in guild.members:
                for role in member.roles:
                    if role.id in role_ids:
                        if member in all_officers:
                            del all_officers[-1]
                        all_officers.append(member)

            # Get a usable number of oficers, and create a dictionary for the count by role
            number_of_officers = len(all_officers)
            number_of_officers_with_each_role = {}

            # For every role in the role list, reverse sorted to preserve higher role:
            for entry in role_ids[::-1]:
                role = guild.get_role(entry)
                if (
                    role is None
                ):  # If the role ID is invalid, let the user know what the role name should be, and that the ID in settings is invalid
                    pass
                else:
                    number_of_officers_with_each_role[
                        role
                    ] = 0  # Create entry in the dictionary

            # This actually counts the officers per role
            for officer in all_officers:
                for role in number_of_officers_with_each_role:
                    if role in officer.roles:
                        number_of_officers_with_each_role[role] += 1
                        break
            pattern = re.compile(r"(LPD )?(\w+( \w+)*)")
            # Reverse the order of the dictionary, since we reversed the list earlier. This preserves the previous output of Cadet first, Chief last
            number_of_officers_with_each_role = dict(
                reversed(list(number_of_officers_with_each_role.items()))
            )

            # Make the embed look pretty with actual role names in server
            role_list = []

            for role in number_of_officers_with_each_role:
                match = pattern.findall(role.name)
                if match:
                    name = "".join(match[0][1]) + "s"
                else:
                    name = role.name

                role_list.append(
                    {
                        "id": role.id,
                        "name": name,
                        "count": number_of_officers_with_each_role[role],
                    }
                )

        return await render_template(
            "officers.html.jinja",
            display_name=user.username,
            title=title,
            role_list=role_list,
            is_moderator=bot.officer_manager.get_officer(user.id).is_white_shirt,
            all_officers=bot.officer_manager.all_officers.values(),
            method=request.method,
            time_results=time_results,
            officer=specified_officer,
        )

    @app.route("/officers_only")
    @requires_authorization
    async def _officers_page():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer:
            return await _403_("Officer")

        return await render_template(
            "under_construction.html.jinja",
            display_name=user.username,
            target="Officers",
        )

    @app.route("/moderation")
    @requires_authorization
    async def _moderation_page():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_white_shirt:
            return await _403_("Moderator")

        return await render_template(
            "under_construction.html.jinja",
            display_name=user.username,
            target="Moderators",
        )

    @app.route("/moderation/loa")
    @requires_authorization
    async def _leave_of_absence():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_white_shirt:
            return await _403_(missing_role="LPD Moderator")

        loa_entries_raw = await bot.officer_manager.get_loa()
        loa_entries = []
        for entry in loa_entries_raw:
            officer = bot.officer_manager.get_officer(entry[0])
            loa_entries.append(
                {
                    "id": entry[0],
                    "name": officer.display_name,
                    "start_date": entry[1],
                    "end_date": entry[2],
                    "reason": entry[3],
                }
            )

        return await render_template(
            "leaves_of_absence.html.jinja",
            display_name=user.username,
            loa_entries=loa_entries,
        )

    @app.route("/moderation/vrclist")
    @requires_authorization
    async def _vrchat_list():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_white_shirt:
            return await _403_("Moderator")

        vrcnames = []
        guild = bot.get_guild(bot.settings["Server_ID"])
        for vrcuser in bot.user_manager.all_users:
            member = guild.get_member(vrcuser[0])
            vrcnames.append({"name": member.display_name, "vrcname": vrcuser[1]})

        return await render_template(
            "vrclist.html.jinja", display_name=user.username, vrcnames=vrcnames
        )

    @app.route("/moderation/rtv", methods=["POST", "GET"])
    @requires_authorization
    async def _rtv():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_white_shirt:
            return await _403_("Moderator")

        role_id_index = []
        rank_ladder = _role_id_index(bot.settings)
        sorted_roles = []
        other_roles = []
        team_roles = []
        trainer_roles = []

        for role_id in rank_ladder:
            sorted_roles.append(bot.officer_manager.guild.get_role(role_id))

        for role in bot.officer_manager.guild.roles:
            if role.name == "@everyone":
                everyone_role_id = role.id
                sorted_roles.insert(0, role)
                continue
            role_id_index.append(role.id)
            if role not in sorted_roles:
                if "team" in role.name.lower():
                    team_roles.append(role)
                elif "trainer" in role.name.lower():
                    trainer_roles.append(role)
                else:
                    other_roles.append(role)

        other_roles.sort(key=lambda x: x.name)
        team_roles.sort(key=lambda x: x.name)
        trainer_roles.sort(key=lambda x: x.name)
        sorted_roles.extend(team_roles)
        sorted_roles.extend(trainer_roles)
        sorted_roles.extend(other_roles)

        rolename = ""
        requested_role_id = ""
        if request.method == "POST":
            data = await request.form
            role_id = data["role_id"]
            requested_role_id = int(role_id)
            if requested_role_id != everyone_role_id:
                role_id_index = []
                role_id_index.append(int(role_id))
                rolename = bot.officer_manager.guild.get_role(int(role_id)).name

        results = []
        for role_id in role_id_index:
            role = bot.officer_manager.guild.get_role(role_id)
            for member in role.members:
                results.append({"name": member.display_name, "role": role.name})

        return await render_template(
            "rtv.html.jinja",
            display_name=user.username,
            results=results,
            method=request.method,
            requested_role_id=requested_role_id,
            rolename=rolename,
            roles=sorted_roles,
        )

    @app.route("/moderation/inactivity", methods=["POST", "GET"])
    @requires_authorization
    async def _mark_inactive():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_white_shirt:
            return await _403_("Moderator")

        role = bot.officer_manager.guild.get_role(bot.settings["inactive_role"])
        if request.method == "POST":
            data = await request.form
            officer_id = int(data["officer_id"])
            officer = bot.officer_manager.get_officer(officer_id)
            await officer.member.add_roles(role)
            return """<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0; url=/moderation/inactivity"></head><body></body></html>"""

        # Get all fields from LeaveTimes
        loa_entries = await bot.officer_manager.get_loa()

        loa_officer_ids = []

        # If the entry is still good, add the officer to our exclusion list. Otherwise, delete the entry if expired.
        for entry in loa_entries:
            loa_officer_ids.append(entry[0])

        # For everyone in the server where their role is in the role ladder,
        # get their last activity times, or if no last activity time, use
        # the time we started monitoring them. Exclude those we have already
        # determined have a valid Leave of Absence

        # Get a date range for our LOAs, and make some dictionaries to work in
        max_inactive_days = bot.settings["max_inactive_days"]
        oldest_valid = datetime.utcnow() - timedelta(days=max_inactive_days)
        inactive_officers = []

        for officer in bot.officer_manager.all_officers.values():
            if officer.id not in loa_officer_ids:
                has_role = False
                if role in officer.member.roles:
                    has_role = True
                last_activity = await officer.get_last_activity(
                    bot.officer_manager.all_monitored_channels
                )
                last_activity = last_activity["time"]
                if last_activity < oldest_valid:
                    inactive_officers.append([officer, last_activity, has_role])

        return await render_template(
            "mark_inactive.html.jinja",
            display_name=user.username,
            inactive_officers=inactive_officers,
            len=len(inactive_officers),
        )

    @app.route("/moderation/patrol_time", methods=["POST", "GET"])
    @requires_authorization
    async def _web_patrol_time():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_white_shirt:
            return await _403_("Moderator")

        now = datetime.utcnow()
        then = datetime.utcnow() - timedelta(days=bot.settings["max_inactive_days"])
        all_officers = list(bot.officer_manager.all_officers.values())

        sort_by = "NAME"
        if request.method == "POST":
            data = await request.form
            sort_by = data["sort_by"]

        multi_line = True

        if sort_by.upper() == "TIME":
            for officer in all_officers:
                officer.seconds = await officer.get_time(then, now)
            all_officers.sort(key=lambda officer: officer.seconds, reverse=True)
        elif sort_by.upper() == "NAME":
            all_officers.sort(key=lambda officer: officer.display_name)
        elif sort_by.upper() == "ID":
            all_officers.sort(key=lambda officer: officer.id)

        data = []
        for officer in all_officers:
            seconds = await officer.get_time(then, now)
            divisions = [60, 60, 24, 7]
            calculations = [[seconds]]
            for i in range(0, len(divisions)):
                second_if_end, first = divmod(calculations[i][0], divisions[i])
                calculations[i].append(first)
                calculations.append([second_if_end])
            return_str = ""
            time_names = ["Seconds", "Minutes", "Hours", "Days", "Weeks"]
            for i in range(0, 5):

                # Determine the fetch num
                if i + 1 == 5:
                    fetch_num = 0
                else:
                    fetch_num = 1
                if multi_line:
                    # End the loop if everything after will be 0
                    if calculations[i][0] == 0 and i != 0:
                        break
                    return_str = (
                        f"{time_names[i]}: {calculations[i][fetch_num]}\n{return_str}"
                    )
                else:
                    if i == 0:
                        return_str = f"{calculations[i][fetch_num]}"
                    else:
                        return_str = f"{calculations[i][fetch_num]}:{return_str}"

            data.append(
                {
                    "name": officer.display_name,
                    "id": officer.id,
                    "return_str": return_str,
                }
            )

        return await render_template(
            "web_patrol_time.html.jinja",
            display_name=user.username,
            sort_by=sort_by.upper(),
            data=data,
        )

    @app.route("/moderation/rank_last_active", methods=["POST", "GET"])
    @requires_authorization
    async def _web_rank_last_active():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_white_shirt:
            return await _403_("Moderator")

        roles = []
        role_ids = _role_id_index(bot.settings)

        for role_id in role_ids:
            roles.append(bot.officer_manager.guild.get_role(role_id))

        last_activity_list = []

        if request.method == "POST":
            data = await request.form
            role_id = data["role_id"]
            role = bot.officer_manager.guild.get_role(int(role_id))

            for member in role.members:
                officer = bot.officer_manager.get_officer(member.id)

                result = await officer.get_all_activity(
                    bot.officer_manager.all_monitored_channels
                )

                # Send the embed
                time_results = sorted(
                    result,
                    key=lambda x: time.mktime(x["time"].timetuple()),
                    reverse=True,
                )

                last_activity_list.append(
                    {"name": officer.display_name, "date": time_results[0]["time"]}
                )

            return await render_template(
                "last_active.html.jinja",
                display_name=user.username,
                roles=roles,
                last_activity_list=last_activity_list,
                requested_role=role,
            )

        for officer in bot.officer_manager.all_officers.values():

            result = await officer.get_all_activity(
                bot.officer_manager.all_monitored_channels
            )

            # Send the embed
            time_results = sorted(
                result, key=lambda x: time.mktime(x["time"].timetuple()), reverse=True
            )

            last_activity_list.append(
                {"name": officer.display_name, "date": time_results[0]["time"]}
            )

        return await render_template(
            "last_active.html.jinja",
            display_name=user.username,
            roles=roles,
            last_activity_list=last_activity_list,
            requested_role=None,
        )

    @app.route("/dispatch/spa", methods=["GET", "POST"])
    @requires_authorization
    async def _dispatch_single_page_():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)

        if (
            not officer.is_dispatch
            and not officer.is_programming_team
            and not officer.is_event_host
        ):
            return await _403_("Dispatch")

        if request.method == "POST":
            data = await request.form
            squad_id = data["squad_id"]
            if (
                officer.member.voice is not None
                and officer.member.voice.channel is not None
            ):
                await officer.member.move_to(
                    bot.officer_manager.guild.get_channel(int(squad_id)),
                    reason=f"{officer.display_name} moved themself through the online Dispatch Portal",
                )

        squad_ids = {}
        for vc in bot.officer_manager.guild.voice_channels:
            if (
                vc.category_id == bot.settings["on_duty_category"]
                and "train" not in vc.name.lower()
            ):
                squad_ids[vc.id] = vc

        return await render_template(
            "dispatch_spa.html.jinja", display_name=user.username, squad_ids=squad_ids
        )

    @app.route("/dispatch/spa/backupCalls.asp", methods=["GET", "HEAD"])
    @requires_authorization
    async def _dispatch_spa_backupCalls():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)

        if not officer.is_dispatch and not officer.is_programming_team:
            return ""

        dispatch_logs = await bot.dispatch_log.get()

        return await render_template(
            "dispatch_backupCalls.asp.jinja", dispatch_logs=dispatch_logs
        )

    @app.route("/dispatch/spa/data.asp", methods=["GET", "HEAD"])
    @requires_authorization
    async def _dispatch_spa_asp():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)

        if not officer.is_dispatch and not officer.is_programming_team:
            return ""

        data = {}
        for vc in bot.officer_manager.guild.voice_channels:
            if (
                vc.category_id == bot.settings["on_duty_category"]
                and "train" not in vc.name.lower()
            ):
                data[vc.id] = [vc, []]

        for officer in bot.officer_manager.all_officers.values():
            display_name = officer.display_name
            if not officer.is_on_duty:
                continue

            if officer.event_squad is not None:
                if officer.event_squad is not officer.squad:
                    display_name = (
                        f"{officer.event_squad.name} - {officer.display_name}"
                    )
                else:
                    display_name = officer.display_name

            data[officer.squad.id][1].append([officer, display_name])

        for squad_id in data:
            data[squad_id][1] = sorted(data[squad_id][1], key=lambda x: x[1])

        data = OrderedDict(sorted(data.items(), key=lambda x: x[1][0].position))

        return await render_template("dispatch_data.asp.jinja", data=data)

    @app.route("/dispatch/spa/backup_request", methods=["POST"])
    @requires_authorization
    async def _dispatch_backup_request():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)

        if not officer:
            return '<meta http-equiv="refresh" content="5; URL=/" />'

        if not officer.is_dispatch and not officer.is_programming_team:
            return '<meta http-equiv="refresh" content="5; URL=/" />'

        data = await request.form
        squad_id = int(data["squad_id"])
        backup_type = data["backup_type"]
        world_name = data["world_name"]
        situation = data["situation"]

        await bot.dispatch_log.create(
            squad_id,
            backup_type,
            world_name,
            situation,
            officer.display_name,
            user.avatar_url,
        )

        return '<meta http-equiv="refresh" content="5; URL=/dispatch/spa" />'

    @app.route("/dispatch/spa/log_complete", methods=["POST"])
    @requires_authorization
    async def _dispatch_log_complete():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)

        if not officer:
            return '<meta http-equiv="refresh" content="5; URL=/" />'

        if not officer.is_dispatch and not officer.is_programming_team:
            return '<meta http-equiv="refresh" content="5; URL=/" />'

        data = await request.form
        message_id = int(data["message_id"])

        success = await bot.dispatch_log.complete(message_id)

        if success:
            return '<meta http-equiv="refresh" content="0; URL=/dispatch/spa" />'
        else:
            return '''<script>alert('Could not update that entry! Has it been deleted?'); window.location = '/dispatch/spa';</script>"'''

    @app.route("/roomba/killcount/upload")
    async def _increment_roomba_killcount_():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        killcount = await bot.sql.request("SELECT count FROM Roomba")
        killcount = killcount[0][0]
        if request.method == "HEAD":
            try:
                killcount = killcount + 1
            except:
                killcount = 1
            await bot.sql.request("DELETE FROM Roomba")
            await bot.sql.request("INSERT INTO Roomba VALUES (%s)", killcount)

            channel = bot.get_channel(bot.settings["error_log_channel"])
            await channel.send(f"""The Roomba has {killcount} kills.""")

        content = """<html>
                    <head>
                    <script>
                        window.stop()
                    </script>
                    </head>
                    <body>
                    </body>
                    </html>"""

        return content

    #######################################################################################################
    #                                   #
    #   API endpoints go below here     #
    #                                   #
    #     Please note that all API      #
    # responses should be returned as   #
    # JSON. You can do this by defining #
    # a dictionary, specifying the keys #
    # in the order you want them        #
    # displayed. Define one dictionary  #
    # per row, and then enclose all of  #
    # them into one dictionary, indexed #
    # in the order you want rows to     #
    # appear.                           #
    #                                   #
    # End your API endpoint function    #
    # with the following:               #
    #                                   #
    # return json.dumps(dict_of_dicts)  #
    #                                   #
    # See below for example             #
    #                                   #
    #####################################
    #
    # @app.route("/api/[ action | resource ]/path_to_endpoint")
    # async def my_api_endpoint():        # This function name should follow the naming convention
    #                                     # of actionorresource_level1_level2_level3_etc_endpoint()
    #     row1 = {}
    #     row1['name'] = "Darth Vader"
    #     row1['team'] = "Sith"
    #     row1['power'] = "Over 9000"
    #     row2 = {}
    #     row2['name'] = "Luke Skywalker"
    #     row2['team'] = "Jedi"
    #     row2['power'] = "Less than 9000"
    #
    #     returnDict = {}
    #     returnDict['1'] = row1
    #     returnDict['2'] = row2
    #
    #     return json.dumps(returnDict)
    #
    #######################################################################################################

    # Action section

    @app.route("/api/action")
    async def action():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        return "Not implemented"

    @app.route("/api/action/shutdown")
    @requires_authorization
    async def action_shutdown():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)

        if not officer:
            return {"authenticacted": False, "shutdown": False}

        if officer.is_programming_team:
            await clean_shutdown(bot, "Web API", officer.display_name)
            return {"authenticacted": True, "shutdown": True}

        return {"authenticacted": True, "shutdown": False}

    # Resource section

    @app.route("/api/resource")
    async def resource():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        return "Not implemented"

    @app.route("/api/resource/auth")
    async def resource_auth():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        encoded_username = request.args.get("vrcuser")
        w = request.args.get("w")
        h = request.args.get("h")
        W = request.args.get("W")
        H = request.args.get("H")

        if not w:
            if not W or int(W) <= 8:
                w = 8
            else:
                w = w
        if not h:
            if not H or int(H) <= 8:
                h = 8
            else:
                h = H

        w = int(w) if int(w) > 8 else 8
        h = int(h) if int(h) > 8 else 8

        officer_id = bot.user_manager.get_discord_by_vrc(dec(encoded_username))

        # Destructo's officer_id for debugging
        # officer_id = 249404332447891456

        # Hroi's officer_id for debugging
        # officer_id = 378666988412731404

        officer = bot.officer_manager.get_officer(officer_id)

        if officer == None:
            render_array(None, filename="/tmp/APITextemp.gif", w=w, h=h)
        else:
            render_array(officer, filename="/tmp/APITextemp.gif", w=w, h=h)

        # Convert to webm
        clip = mp.VideoFileClip("/tmp/APITextemp.gif")
        clip.write_videofile("/tmp/APITextemp.webm", verbose=False, logger=None)

        # Return the webm
        response = await send_file("/tmp/APITextemp.webm")
        response.content_type = "video/webm"

        return response

    @app.route("/api/resource/auth/urls")
    async def resource_auth_urls():
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        users = []
        for user in bot.user_manager.all_users:
            username = user[1]
            users.append(username)

        urls = geturls(users, useDict=True)
        return json.dumps(urls)

    @app.route("/spa")
    async def spa():
        return await send_file("lpd-officer-monitor/public/index.html")
        return await render_template("spa.html")

    @app.route("/vue.js")
    async def vuejs():
        return await send_file("lpd-officer-monitor/public/vue.js")
