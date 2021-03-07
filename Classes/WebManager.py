import asyncio
import nest_asyncio

nest_asyncio.apply()

import time

from quart import Quart, redirect, url_for, request
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized

from Classes.commands import (
    Time,
    Inactivity,
    VRChatAccoutLink,
    Applications,
    Moderation,
    Other,
)

app = Quart("LPD Officer Monitor")

HTML_HEAD = """<!DOCTYPE html>
            <HTML lang="en" xmlns="http://www.w3.org/1999/xhtml">
            <HEAD>
                <meta charset="utf-8" />
                <TITLE>{}</TITLE>
                <style>
                    a:link,a:visited {{color: Blue; background-color: White; text-decoration: underline; target-new: none;}}
                    a:hover {{color: Blue; background-color: Yellow; text-decoration: underline; target-new: none;}}
                    .btn-link {{border: none; outline: none; background: none; cursor: pointer; color: #0000EE; padding: 0; text-decoration: underline; font-family: inherit; font-size: inherit;}}
                </style>
            </HEAD>"""

NAVBAR = """<div class="topnav">
                    <a class="active" href="/">Home</a>
                    <a href="/login">Login</a>
                    <a href="/officers">Officers</a>
                    <a href="/officers_only">Officers only</a>
                    <a href="/moderation">Moderation</a>
            </div>"""

HTML_FOOT = """</HTML>"""


@app.route("/callback/")
async def callback():
    await discord.callback()
    return redirect(url_for(".me"))


@app.errorhandler(Unauthorized)
async def redirect_unauthorized(e):
    return redirect(url_for("login"))


@app.route("/me/")
@requires_authorization
async def me():
    user = await discord.fetch_user()
    return f"""
    <html>
        <head>
            <title>{user.name}</title>
        </head>
        <body>
            <img src='{user.avatar_url}' />
        </body>
    </html>"""


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

    @app.route("/callback/")
    async def _callback():
        await discord.callback()
        return redirect(url_for("/"))

    @app.errorhandler(Unauthorized)
    async def redirect_unauthorized(e):
        return redirect(url_for("login"))

    # @app.route("/me/")
    # @requires_authorization
    # async def _me():
    #     user = await discord.fetch_user()
    #     return f"""{HTML_HEAD.format(user.name)}
    #         <body>
    #             <img src='{user.avatar_url}' />
    #         </body>
    #         {HTML_FOOT}"""

    @app.route("/")
    async def home():
        content = f"""{HTML_HEAD.format('Welcome to the LPD!')}
            <body>
            {NAVBAR}
                Welcome to the home page!
            </body>
            {HTML_FOOT}"""
        return content

    @app.route("/login/")
    async def login():
        return await discord.create_session()

    @app.route("/officers")
    @requires_authorization
    async def display_officers():

        user = await discord.fetch_user()
        content = f"""{HTML_HEAD.format('Table of Officers')}
            <body>
            {NAVBAR}
            Welcome {user.name} - your ID  is {user.id}<br><br>
            <table style="width:100%">
            <tr>
                <th>Officer ID</th>
                <th>Name</th>
                <th>On Duty?</th>
                <th>Squad</th>
            </tr>"""

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
                    </table></body>{HTML_FOOT}"""

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
            <body>
            {NAVBAR}
            Sorry, this page is restricted to Officers of the LPD only.
            </body>
            {HTML_FOOT}"""

            return content

        content = f"""{HTML_HEAD.format('LPD Officers only')}
        <body>
        {NAVBAR}
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
                <body>
                {NAVBAR}
                Sorry, you're not staff.
                </body>
                {HTML_FOOT}"""

            return content
        content = f"""{HTML_HEAD.format('LPD Moderator Portal')}
            <body>
            {NAVBAR}
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

        if request.method == "POST":
            data = await request.form
        else:
            return """<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0; url=http://http.cat/404"></head><body></body></html>"""

        officer_id = int(data["officer_id"])
        officer = bot.officer_manager.get_officer(officer_id)

        if officer is None:
            content = f"""{HTML_HEAD.format('No such Officer')}{NAVBAR}
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
        TABLE = f"""<table style="width:50%">
            <tr>
            <td>{officer.display_name}</td>
            <td>{officer.id}</td>
            </tr>
            <tr>
            <th>Time</th>
            <th>Location</th>
            </tr>"""
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
            </table>"""

        content = f"""{HTML_HEAD.format('Last Activity')}<BODY>{NAVBAR}{TABLE}</BODY>{HTML_FOOT}"""
        return content
