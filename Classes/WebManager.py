import asyncio
import nest_asyncio

nest_asyncio.apply()

import time
from datetime import datetime, timedelta

from quart import Quart, redirect, url_for, request
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized

from Classes.extra_functions import role_id_index as _role_id_index


# from Classes.commands import (
#     Time,
#     Inactivity,
#     VRChatAccoutLink,
#     Applications,
#     Moderation,
#     Other,
# )

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
                    .navbar {{
                    overflow: hidden;
                    background-color: #333;
                    font-family: Arial;
                    }}

                    /* Links inside the navbar */
                    .navbar a {{
                    float: left;
                    font-size: 16px;
                    color: white;
                    text-align: center;
                    padding: 14px 16px;
                    text-decoration: none;
                    }}

                    /* The dropdown container */
                    .dropdown {{
                    float: left;
                    overflow: hidden;
                    }}

                    /* Dropdown button */
                    .dropdown .dropbtn {{
                    font-size: 16px;
                    border: none;
                    outline: none;
                    color: white;
                    padding: 14px 16px;
                    background-color: inherit;
                    font-family: inherit; /* Important for vertical align on mobile phones */
                    margin: 0; /* Important for vertical align on mobile phones */
                    }}

                    /* Add a red background color to navbar links on hover */
                    .navbar a:hover, .dropdown:hover .dropbtn {{
                    background-color: red;
                    }}

                    /* Dropdown content (hidden by default) */
                    .dropdown-content {{
                    display: none;
                    position: absolute;
                    background-color: #f9f9f9;
                    min-width: 160px;
                    box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
                    z-index: 1;
                    }}

                    /* Links inside the dropdown */
                    .dropdown-content a {{
                    float: none;
                    color: black;
                    padding: 12px 16px;
                    text-decoration: none;
                    display: block;
                    text-align: left;
                    }}

                    /* Add a grey background color to dropdown links on hover */
                    .dropdown-content a:hover {{
                    background-color: #ddd;
                    }}

                    /* Show the dropdown menu on hover */
                    .dropdown:hover .dropdown-content {{
                    display: block;
                    }}
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
                    </div>
                </div>

            </div>"""

HTML_FOOT = """</HTML>"""


class WebManager:
    def __init__(self, bot):

        self.bot = bot

    @classmethod
    async def start(
        cls, Bot, host="0.0.0.0", port=8080, id=None, secret=None, token=None
    ):
        global bot
        bot = Bot
        instance = cls(bot)

        app.secret_key = b"random bytes representing quart secret key"

        app.config["DISCORD_CLIENT_ID"] = id  # Discord client ID.
        app.config["DISCORD_CLIENT_SECRET"] = secret  # Discord client secret.
        app.config[
            "DISCORD_REDIRECT_URI"
        ] = "http://devbox.lolipd.com/callback"  # URL to your callback endpoint.
        app.config["DISCORD_BOT_TOKEN"] = token  # Required to access BOT resources.

        global discord
        discord = DiscordOAuth2Session(app)
        loop = asyncio.get_event_loop()
        app.run(loop=loop, host=host, port=port)

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

    @app.route("/officers")
    @requires_authorization
    async def display_officers():

        user = await discord.fetch_user()
        content = f"""{HTML_HEAD.format('Table of Officers')}
            Welcome {user.name} - your ID  is {user.id}<br><br>
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
                        {f'<td><form action="/api/time/last_active" method="post"><button type="submit" name="officer_id" value="{officer.id}" class="btn-link">Get activity</button></form></td>' if bot.officer_manager.get_officer(user.id).is_white_shirt else ''}
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
            for id in bot.officer_manager.all_officer_ids:
                print(id)
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
        if not officer or not officer.is_white_shirt:
            content = f"""{HTML_HEAD.format('This page is for LPD White Shirts only.')}
                Sorry, you're not staff.
                </body>
                {HTML_FOOT}"""

            return content
        content = f"""{HTML_HEAD.format('LPD Moderator Portal')}
            <h1 style="color: #4485b8;">LPD Moderator portal</h1>
            <p><span style="color: #000000;"><b>This is a test page for LPD Moderators only.</b></span></p>
            <form action="/api/time/last_active" method="POST">
                <label for="officer_id">Officer ID</label>
                <input type="number" id="officer_id" name = "officer_id">
                <input type="submit" value="Get activity">
            </form>
            </body>
            {HTML_FOOT}"""

        return content

    @app.route("/api/time/last_active", methods=["POST", "GET"])
    @requires_authorization
    async def _web_last_active():

        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_white_shirt:
            content = f"""{HTML_HEAD.format('This page is for LPD White Shirts only.')}
                Sorry, you're not staff.
                </body>
                {HTML_FOOT}"""

            return content

        if request.method == "POST":
            data = await request.form
        else:
            return """<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0; url=http://http.cat/404"></head><body></body></html>"""

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

    @app.route("/moderation/loa")
    @requires_authorization
    async def _leave_of_absence():
        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_white_shirt:
            content = f"""{HTML_HEAD.format('This page is for LPD White Shirts only.')}
                Sorry, you're not staff.
                </body>
                {HTML_FOOT}"""

            return content

        loa_entries = await bot.officer_manager.get_loa()

        TABLE = f"""<table class="blueTable">
                    <tr>
                    <th>Officer ID</th>
                    <th>Officer Name</th>
                    <th>Start date</th>
                    <th>End date</th>
                    <th>Reason</th>
                    </tr>"""

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
        if not officer or not officer.is_white_shirt:
            content = f"""{HTML_HEAD.format('This page is for LPD White Shirts only.')}
                Sorry, you're not staff.
                </body>
                {HTML_FOOT}"""

            return content

        TABLE = f"""<table class="blueTable">
                    <tr>
                    <th>Officer name</th>
                    <th>VRChat Name</th>
                    </tr>"""

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

    @app.route("/moderation/rtv")
    @requires_authorization
    async def _rtv():
        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer or not officer.is_white_shirt:
            content = f"""{HTML_HEAD.format('This page is for LPD White Shirts only.')}
                Sorry, you're not staff.
                </body>
                {HTML_FOOT}"""

            return content

        role_id_index = _role_id_index(bot.settings)

        TABLE = f"""<table class="blueTable">
                    <tr>
                    <th>Officer Name</th>
                    <th>Rank</th>
                    </tr>
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
        if not officer or not officer.is_white_shirt:
            content = f"""{HTML_HEAD.format('This page is for LPD White Shirts only.')}
                Sorry, you're not staff.
                </body>
                {HTML_FOOT}"""

            return content

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
                # except:
                #     pass
                #     return f"""{HTML_HEAD.format('Inactivity - NO DATA')}<br><br>It looks like there isn't any patrol data... </body>{HTML_FOOT}"""

        if len(inactive_officers) == 0:
            return f"""{HTML_HEAD.format('Inactivity - NONE INACTIVE')}<br><br>It doesn't look like there are any inactive officers!</body>{HTML_FOOT}"""

        TABLE = f"""<table class="blueTable">
                    <tr>
                    <th>Officer name</th>
                    <th>Last activity</th>
                    <th>Already Marked</th>
                    <th>Mark Inactive</th>
                    </tr>"""

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
