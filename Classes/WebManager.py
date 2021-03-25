import asyncio
import nest_asyncio

nest_asyncio.apply()

import time
from datetime import datetime, timedelta
import re
import moviepy.editor as mp
from urllib.parse import unquote_plus as dec

from quart import Quart, redirect, url_for, request, send_file
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized

from Classes.extra_functions import role_id_index as _role_id_index
from Classes.APITex import render_array


app = Quart("LPD Officer Monitor")

HTML_HEAD = """<!DOCTYPE html>
            <HTML lang="en" xmlns="http://www.w3.org/1999/xhtml">
            <HEAD>
                <meta charset="utf-8" />
                <TITLE>{}</TITLE>
                <style>
                    .btn-link {{border: none; outline: none; background: none; cursor: pointer; color: #0000EE; padding: 0; text-decoration: underline; font-family: inherit; font-size: inherit;}}
                    table.blueTable {{border: 1px solid #1C6EA4; background-color: #EEEEEE; width: 80%; text-align: left; border-collapse: collapse;}}
                    table.blueTable td, table.blueTable th {{border: 1px solid #AAAAAA; padding: 3px 2px;}}
                    table.blueTable tbody td {{font-size: 13px;}}
                    table.blueTable tr:nth-child(even) {{background: #D0E4F5;}}
                    table.blueTable thead {{background: #1C6EA4; background: -moz-linear-gradient(top, #5592bb 0%, #327cad 66%, #1C6EA4 100%); background: -webkit-linear-gradient(top, #5592bb 0%, #327cad 66%, #1C6EA4 100%); background: linear-gradient(to bottom, #5592bb 0%, #327cad 66%, #1C6EA4 100%); border-bottom: 2px solid #444444;}}
                    table.blueTable thead th {{font-size: 15px; font-weight: bold;  color: #FFFFFF;  border-left: 2px solid #D0E4F5;}}
                    table.blueTable thead th:first-child {{border-left: none;}}
                    table.blueTable tfoot td {{font-size: 14px;}}
                    table.blueTable tfoot .links {{text-align: right;}}
                    table.blueTable tfoot .links a{{display: inline-block; background: #1C6EA4; color: #FFFFFF; padding: 2px 8px; border-radius: 5px;}}
                    
                    /* Navbar container */
                    .navbar {{overflow: hidden; background-color: #333; font-family: Arial;}}

                    /* Links inside the navbar */
                    .navbar a {{float: left; font-size: 16px; color: white; text-align: center; padding: 14px 16px; text-decoration: none;}}

                    /* The dropdown container */
                    .dropdown {{float: left; overflow: hidden;}}

                    /* Dropdown button */
                    .dropdown .dropbtn {{font-size: 16px; border: none; outline: none; color: white; padding: 14px 16px; background-color: inherit; font-family: inherit; margin: 0;}}

                    /* Add a red background color to navbar links on hover */
                    .navbar a:hover, .dropdown:hover .dropbtn {{background-color: red;}}

                    /* Dropdown content (hidden by default) */
                    .dropdown-content {{display: none; position: absolute; background-color: #f9f9f9; min-width: 160px; box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2); z-index: 1;}}

                    /* Links inside the dropdown */
                    .dropdown-content a {{float: none; color: black; padding: 12px 16px; text-decoration: none; display: block; text-align: left;}}

                    /* Add a grey background color to dropdown links on hover */
                    .dropdown-content a:hover {{background-color: #ddd;}}

                    /* Show the dropdown menu on hover */
                    .dropdown:hover .dropdown-content {{display: block;}}

                    .flex-container {{padding: 0; margin: 0; list-style: none; border: 1px solid silver; -ms-box-orient: horizontal; display: -webkit-box; display: -moz-box; display: -ms-flexbox; display: -moz-flex; display: -webkit-flex; display: flex;}}

                    .flex-item {{padding: 5px; width: 400px; margin: 10px; }}

                    .wrap    {{-webkit-flex-wrap: wrap; flex-wrap: wrap;}}  

                    .wrap li {{background: gold;}}
                    
                </style>
                <link rel='icon' href='https://static.wikia.nocookie.net/vrchat-legends/images/1/1e/LPD_Logo_low.png/revision/latest?cb=20200401012542' type='image/x-icon'/ >
            </HEAD>
            <BODY>
            <div class="navbar">
                <a href="/">Home</a>
                <a href="/login">Login</a>
                <a href="/officers">Officers</a>
                <a href="/officers_only">Officers only</a>
                
                <div class="dropdown">
                    <button class="dropbtn">Moderation &darr;
                    </button>
                    
                    <div class="dropdown-content">
                        <a href="/moderation">Moderation</a>
                        <a href="/moderation/loa">Leaves of Absence</a>
                        <a href="/moderation/vrclist">VRChat Name List</a>
                        <a href="/moderation/rtv">Officers by Role</a>
                        <a href="/moderation/inactivity">Inactive Officers</a>
                        <a href="/moderation/patrol_time">Patrol Time</a>
                        <a href="/moderation/rank_last_active">Last Activity by Rank</a>
                    </div>
                </div>

                <div class="dropdown">
                    <button class="dropbtn">Dispatch &darr;
                    </button>
                    
                    <div class="dropdown-content">
                        <a href="/dispatch">Dispatch</a>
                        
                        
                    </div>
                </div>

                <a href="https://teamup.com/ksfnmscvrenv3hkk32">Event Calendar</a>

            </div>""" #  height: 100px;line-height: 100px; 

HTML_FOOT = """</HTML>"""

def _403_(missing_role):
    title = f'This page is for LPD {missing_role} only'
    return f"""{HTML_HEAD.format(title)}
                Sorry, you're not {missing_role}.
                </body>
                {HTML_FOOT}"""

class WebManager:
    def __init__(self, bot):

        self.bot = bot

    @classmethod
    async def start(
        cls, Bot, host="0.0.0.0", port=443, id=None, secret=None, token=None, callback=None
    ):
        global bot
        global discord

        bot = Bot
        instance = cls(bot)

        app.secret_key = b"random bytes representing quart secret key"

        app.config["DISCORD_CLIENT_ID"] = id  # Discord client ID.
        app.config["DISCORD_CLIENT_SECRET"] = secret  # Discord client secret.
        app.config["DISCORD_REDIRECT_URI"] = callback  # URL to your callback endpoint.
        app.config["DISCORD_BOT_TOKEN"] = token  # Required to access BOT resources.

        discord = DiscordOAuth2Session(app)
        loop = asyncio.get_event_loop()
        app.run(loop=loop, host=host, port=port, certfile='/etc/letsencrypt/live/devbox.lolipd.com/cert.pem', keyfile='/etc/letsencrypt/live/devbox.lolipd.com/privkey.pem')

    @app.route("/login/")
    async def login():
        return await discord.create_session()

    @app.route("/callback/")
    async def _callback():
        await discord.callback()
        return redirect(url_for(".home"))

    @app.errorhandler(Unauthorized)
    async def redirect_unauthorized(e):
        return redirect(url_for("login"))

    @app.route("/")
    async def home():
        content = f"""{HTML_HEAD.format('Welcome to the LPD!')}
                Welcome to the home page!
            </body>
            {HTML_FOOT}"""
        return content

    @app.route("/officers", methods=["POST", "GET"])
    @requires_authorization
    async def display_officers():
        user = await discord.fetch_user()

        if request.method == "POST":
            user = await discord.fetch_user()
            officer = bot.officer_manager.get_officer(user.id)
            if not officer or not officer.is_moderator:
                content = f"""{HTML_HEAD.format('This page is for LPD Moderators only.')}
                    Sorry, you're not staff.
                    </body>
                    {HTML_FOOT}"""

                return content
            
            data = await request.form
            officer_id = int(data["officer_id"])
            officer = bot.officer_manager.get_officer(officer_id)

            if officer is None:
                content = f"""{HTML_HEAD.format('No such Officer')}
                    The officer you have requested does not exist. Please make sure the ID is correct.
                    </body>{HTML_FOOT}"""
                return content

            # Get the time
            result = await officer.get_all_activity(
                bot.officer_manager.all_monitored_channels
            )

            # Send the embed
            time_results = sorted(
                result, key=lambda x: time.mktime(x["time"].timetuple()), reverse=True
            )
            TABLE = f"""<table class="blueTable">
                <thead>
                <tr>
                <th>{officer.display_name}</th>
                <th>{officer.id}</th>
                </tr>
                <tr></tr>
                <tr>
                <th>Time</th>
                <th>Location</th>
                </tr>
                </thead>
                <tbody>"""
            for result in time_results:
                if result["channel_id"] == None:
                    TABLE = f"""{TABLE}
                        <tr>
                        <td>{result['time']}</td>
                        <td>{result['other_activity']}</td>
                        </tr>
                        """
                else:
                    TABLE = f"""{TABLE}
                        <tr>
                        <td>{result['time']}</td>
                        <td>{bot.get_channel(result['channel_id']).name}</td>
                        <tr>
                        """
            TABLE = f"""{TABLE}
                </tbody></table>"""

            content = f"""{HTML_HEAD.format('Last Activity')}{TABLE}</BODY>{HTML_FOOT}"""
            return content

        count_officers = """<table class="blueTable">
                          <thead><tr><th>Rank</th>
                          <th>Count</th></tr></thead>"""
        if bot.officer_manager.get_officer(user.id).is_moderator:
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
                    number_of_officers_with_each_role[role] = 0  # Create entry in the dictionary

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
            for role in number_of_officers_with_each_role:

                match = pattern.findall(role.name)
                if match:
                    name = "".join(match[0][1]) + "s"

                else:
                    name = role.name

                count_officers = f"""{count_officers}
                                     <tr>
                                     <td><form action="/moderation/rtv" method="post"><button type="submit" name="role_id" value="{role.id}" class="btn-link">{name}</button></form></td>
                                     <td>{number_of_officers_with_each_role[role]}</td>
                                     </tr>"""
        
        count_officers = f"""{count_officers}</table><br><br>"""

        content = f"""{HTML_HEAD.format('Table of Officers')}
            {count_officers if bot.officer_manager.get_officer(user.id).is_moderator else ''}
            <table class="blueTable">
            <thead>
            <tr>
                <th>Officer ID</th>
                <th>Name</th>
                <th>On Duty?</th>
                <th>Squad</th>
                <th>Get last_activity</th>
            </tr>
            </thead>

            <tbody>"""

        for officer in bot.officer_manager.all_officers:
            content = f"""{content}
                        <tr>
                        <td>{officer.id}</td>
                        <td>{officer.display_name}</td>
                        <td>{officer.is_on_duty}</td>
                        <td>{officer.squad}</td>
                        {f'<td><form action="/officers" method="post"><button type="submit" name="officer_id" value="{officer.id}" class="btn-link">Get activity</button></form></td>' if bot.officer_manager.get_officer(user.id).is_moderator else ''}
                        </tr>"""
        content = f"""{content}
                    </tbody></table></body>{HTML_FOOT}"""

        return content

    @app.route("/officers_only")
    @requires_authorization
    async def _officers_page():
        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer:
            content = f"""{HTML_HEAD.format('This page is restricted to LPD Officers only')}
            Sorry, this page is restricted to Officers of the LPD only.
            </body>
            {HTML_FOOT}"""

            return content

        content = f"""{HTML_HEAD.format('LPD Officers only')}
        This page is for LPD Officers only. It looks like you're an officer, so welcome!
        </body>
        {HTML_FOOT}"""

        return content

    @app.route("/moderation")
    @requires_authorization
    async def _moderation_page():
        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_moderator:
            return _403_('Moderator')

        content = f"""{HTML_HEAD.format('LPD Moderator Portal')}
            <h1 style="color: #4485b8;">LPD Moderator portal</h1>
            <p><span style="color: #000000;"><b>This is a test page for LPD Moderators only.</b></span></p>
            </body>
            {HTML_FOOT}"""

        return content

    @app.route("/moderation/loa")
    @requires_authorization
    async def _leave_of_absence():
        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_moderator:
            return _403_('Moderator')

        loa_entries = await bot.officer_manager.get_loa()

        TABLE = f"""<table class="blueTable">
                    <thead><tr>
                    <th>Officer ID</th>
                    <th>Officer Name</th>
                    <th>Start date</th>
                    <th>End date</th>
                    <th>Reason</th>
                    </thead></tr>"""

        for entry in loa_entries:
            officer = bot.officer_manager.get_officer(entry[0])
            TABLE = f"""{TABLE}
                        <tr>
                        <td>{entry[0]}</td>
                        <td>{officer.display_name}
                        <td>{entry[1]}</td>
                        <td>{entry[2]}</td>
                        <td>{entry[3]}</td>
                        </tr>"""

        content = f"""{HTML_HEAD.format('Leave of Absence Entries')}
                      {TABLE}
                      </TABLE>
                      </BODY>
                      {HTML_FOOT}"""

        return content

    @app.route("/moderation/vrclist")
    @requires_authorization
    async def _vrchat_list():
        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_moderator:
            return _403_('Moderator')

        TABLE = f"""<table class="blueTable">
                    <thead><tr>
                    <th>Officer name</th>
                    <th>VRChat Name</th>
                    </thead></tr>"""

        guild = bot.get_guild(bot.settings["Server_ID"])
        for vrcuser in bot.user_manager.all_users:
            member = guild.get_member(vrcuser[0])
            TABLE = f"""{TABLE}
                        <tr>
                        <td>{member.display_name}</td>
                        <td>{vrcuser[1]}</td>
                        </tr>"""

        content = f"""{HTML_HEAD.format('VRChat Name List')}
                      {TABLE}
                      </TABLE>
                      </BODY>
                      {HTML_FOOT}"""

        return content

    @app.route("/moderation/rtv", methods=["POST", "GET"])
    @requires_authorization
    async def _rtv():
        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_moderator:
            return _403_('Moderator')
        
        role_id_index = _role_id_index(bot.settings)
        
        if request.method == "POST":
            data = await request.form
            role_id = data["role_id"]
            role_id_index = []
            role_id_index.append(int(role_id))
        
        TABLE = f"""<table class="blueTable">
                    <thead><tr>
                    <th>Officer Name</th>
                    <th>Rank</th>
                    </thead></tr>
                    """

        for role_id in role_id_index:
            role = bot.officer_manager.guild.get_role(role_id)
            for member in role.members:
                TABLE = f"""{TABLE}
                            <tr>
                            <td>{member.display_name}</td>
                            <td>{role.name}</td>
                            </tr>"""

        content = f"""{HTML_HEAD.format('LPD Members by Rank')}
                      {TABLE}
                      </TABLE>
                      </BODY>
                      {HTML_FOOT}"""

        return content

    @app.route("/moderation/inactivity", methods=["POST", "GET"])
    @requires_authorization
    async def _mark_inactive():
        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_moderator:
            return _403_('Moderator')

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

        for officer in bot.officer_manager.all_officers:
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

        if len(inactive_officers) == 0:
            return f"""{HTML_HEAD.format('Inactivity - NONE INACTIVE')}<br><br>It doesn't look like there are any inactive officers!</body>{HTML_FOOT}"""

        TABLE = f"""<table class="blueTable">
                    <thead><tr>
                    <th>Officer name</th>
                    <th>Last activity</th>
                    <th>Already Marked</th>
                    <th>Mark Inactive</th>
                    </thead></tr>"""

        for officer in inactive_officers:
            TABLE = f"""{TABLE}
                        <tr>
                        <td>{officer[0].display_name}</td>
                        <td>{officer[1]}</td>
                        <td>{'Yes' if officer[2] else 'No'}</td>
                        {f'<td><form action="/moderation/inactivity" method="post"><button type="submit" name="officer_id" value="{officer[0].id}" class="btn-link">Mark inactive</button></form></td>' if not officer[2] else ''}
                        </tr>"""

        content = f"""{HTML_HEAD.format('Inactive Officers')}
                      {TABLE}
                      </TABLE>
                      </BODY>
                      {HTML_FOOT}"""

        return content

    @app.route('/moderation/patrol_time', methods=["POST", "GET"])
    @requires_authorization
    async def _web_patrol_time():
        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_moderator:
            return _403_('Moderator')

        now = datetime.utcnow()
        then = datetime.utcnow() - timedelta(days=bot.settings["max_inactive_days"])
        all_officers = bot.officer_manager.all_officers

        sort_by = "NAME"
        if request.method == "POST":
            data = await request.form
            sort_by = data["sort_by"]
            

        
        content = f"""{HTML_HEAD.format('Patrol Times by ' + sort_by.upper())}
                      <table class="blueTable">
                      <thead>
                      <tr>
                      <th><form action="/moderation/patrol_time" method="post"><button type="submit" name="sort_by" value="name" class="btn-link">Name</button></form></th>
                      <th><form action="/moderation/patrol_time" method="post"><button type="submit" name="sort_by" value="id" class="btn-link">Officer ID</button></form></th>
                      <th><form action="/moderation/patrol_time" method="post"><button type="submit" name="sort_by" value="time" class="btn-link">Time</button></form></th>
                      </tr>
                      </thead>"""

        multi_line = True

        if sort_by.upper() == "TIME":
            for officer in all_officers:
                officer.seconds = await officer.get_time(then, now)
            all_officers.sort(key=lambda officer: officer.seconds, reverse=True)
        elif sort_by.upper() == "NAME":
            all_officers.sort(key=lambda officer: officer.display_name)
        elif sort_by.upper() == "ID":
            all_officers.sort(key=lambda officer: officer.id)

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
            

            content = f"""{content}
                          <tr>
                          <td>{officer.display_name}</td>
                          <td>{officer.id}</td>
                          <td>{return_str}</td>
                          </tr>"""

        content = f"""{content}
                      </table>
                      {HTML_FOOT}"""
        
        return content

    @app.route('/moderation/rank_last_active', methods=["POST", "GET"])
    @requires_authorization
    async def _web_rank_last_active():
        
        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_moderator:
            return _403_.format('Moderator')
        
        this_func_navbar = """<table>
                              <thead>"""

        role_ids = _role_id_index(bot.settings)

        for role_id in role_ids:
            this_func_navbar = f"""{this_func_navbar}
                                   <tr>
                                   <th><form action="/moderation/rank_last_active" method="post"><button type="submit" name="role_id" value="{role_id}" class="btn-link">{bot.officer_manager.guild.get_role(role_id).name}</button></form></th>
                                   </tr>"""
        this_func_navbar = f"""{this_func_navbar}
                               </thead>
                               </table><br><br>"""

        if request.method == "POST":
            data = await request.form
            role_id = data["role_id"]
            role = bot.officer_manager.guild.get_role(int(role_id))

            TABLE = f"""<table class="blueTable">
                    <thead>
                    <tr>
                    <th>{role.name}</th>
                    <th></th>
                    </tr>
                    <tr></tr>
                    <tr>
                    <th>Name</th>
                    <th>Last Active</th>
                    </tr>
                    </thead>
                    <tbody>"""
            
            for member in role.members:
                officer = bot.officer_manager.get_officer(member.id)
                
                result = await officer.get_all_activity(
                    bot.officer_manager.all_monitored_channels
                )

                # Send the embed
                time_results = sorted(
                    result, key=lambda x: time.mktime(x["time"].timetuple()), reverse=True
                )
                
                result = time_results[0]
                
                TABLE = f"""{TABLE}
                    <tr>
                    <td>{officer.display_name}</td>
                    <td>{result['time']}</td>
                    <tr>
                    """

            TABLE = f"""{TABLE}
                </tbody></table>"""

            content = f"""{HTML_HEAD.format('Last Activity by Rank')}{this_func_navbar}{TABLE}</BODY>{HTML_FOOT}"""
            return content

        TABLE = f"""<table class="blueTable">
                    <thead>
                    <tr>
                    <th>Name</th>
                    <th>Last Active</th>
                    </tr>
                    </thead>
                    <tbody>"""
            
        for officer in bot.officer_manager.all_officers:
            
            result = await officer.get_all_activity(
                bot.officer_manager.all_monitored_channels
            )

            # Send the embed
            time_results = sorted(
                result, key=lambda x: time.mktime(x["time"].timetuple()), reverse=True
            )
            
            result = time_results[0]
            
            TABLE = f"""{TABLE}
                <tr>
                <td>{officer.display_name}</td>
                <td>{result['time']}</td>
                <tr>
                """

        TABLE = f"""{TABLE}
            </tbody></table>"""

        content = f"""{HTML_HEAD.format('Last Activity by Role')}{this_func_navbar}{TABLE}</BODY>{HTML_FOOT}"""
        return content

    @app.route('/dispatch')
    @requires_authorization
    async def _dispatch_main_view():

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)

        if not officer.is_dispatch:
            return _403_('Dispatch')

        on_duty_officers = []
        TABLE = """<ul class="flex-container nowrap">"""

        for officer in bot.officer_manager.all_officers:
            if not officer.is_on_duty:
                continue
            on_duty_officers.append(officer)
        
        on_duty_officers.sort(key=lambda x: x.squad)

        squad = None
        for officer in on_duty_officers:
            if officer.squad != squad:
                if squad != None:
                    TABLE = f"""{TABLE}
                                </table>
                                </li>"""
                TABLE = f"""{TABLE}
                            <li class="flex-item">
                                <table class="blueTable">
                                    <thead>
                                    <tr>
                                        <th>{officer.squad}<th>
                                    </tr>
                                    </thead>"""
            TABLE = f"""{TABLE}
                        <tr>
                        <td>{officer.display_name}</td>
                        </tr>"""
            squad = officer.squad

        TABLE = f"""{TABLE}
                    </table
                    </li>
                    </u1>"""

        content = f"""{HTML_HEAD.format('Dispatch - Squad view')}
                      {TABLE}
                      </body>
                      {HTML_FOOT}"""
        squad = None
        return content

    @app.route('/roomba/killcount/upload')
    async def _increment_roomba_killcount_():
        killcount = await bot.sql.request('SELECT count FROM Roomba')
        killcount = killcount[0][0]
        if request.method == "HEAD":
            try:
                killcount = killcount + 1
            except: 
                killcount = 1
            await bot.sql.request('DELETE FROM Roomba')
            await bot.sql.request('INSERT INTO Roomba VALUES (%s)', killcount)
        
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

    @app.route('/api/auth')
    async def _api_handler_():
        
        encoded_username = request.args.get('vrcuser')
        w = int(request.args.get('w'))
        h = int(request.args.get('h'))
        
        w = w if w > 8 else 8
        h = h if h > 8 else 8

        officer_id = bot.user_manager.get_discord_by_vrc(dec(encoded_username))
        
        # Destructo's officer_id for debugging
        # officer_id = 249404332447891456

        # Hroi's officer_id for debugging
        # officer_id = 378666988412731404
        
        officer = bot.officer_manager.get_officer(officer_id)

        d = {}

        if officer == None:
            is_lpd = False
            d["is_lpd"] = is_lpd
        else:
            is_lpd = True

            d["is_cadet"] = officer.is_cadet
            d["is_white_shirt"] = officer.is_white_shirt
            d["is_lpd"] = is_lpd
            d["is_moderator"] = officer.is_moderator
            d["is_slrt"] = officer.is_slrt_trained
            d["is_slrt_trainer"] = officer.is_slrt_trainer
            d["is_lmt"] = officer.is_lmt_trained
            d["is_lmt_trainer"] = officer.is_lmt_trainer
            d["is_watch_officer"] = officer.is_watch_officer
            d["is_prison_trainer"] = officer.is_prison_trainer
            d["is_instigator"] = officer.is_instigator
            d["is_trainer"] = officer.is_trainer
            d["is_chat_moderator"] = officer.is_chat_moderator
            d["is_event_host"] = officer.is_event_host
            d["is_dev_team"] = officer.is_dev_member
            d["is_media_production"] = officer.is_media_production
            d["is_janitor"] = officer.is_janitor
            d["is_korean"] = officer.is_korean
            d["is_chinese"] = officer.is_chinese
            d["is_inactive"] = officer.is_inactive
            d["is_programming_team"] = officer.is_programming_team


        # Generate a GIF from the permissions
        render_array(d, filename='/tmp/APITextemp.gif', w=w, h=h)
        
        # Convert to webm
        clip = mp.VideoFileClip('/tmp/APITextemp.gif')
        clip.write_videofile('/tmp/APITextemp.webm', verbose=False, logger=None)

        # Return the webm
        response = await send_file('/tmp/APITextemp.webm')
        response.content_type = "video/webm"

        return response