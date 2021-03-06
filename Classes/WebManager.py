import asyncio
import nest_asyncio

nest_asyncio.apply()
from quart import Quart, redirect, url_for
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized

app = Quart("LPD Officer Monitor")

HTML_HEAD = """<!DOCTYPE html>
            <HTML lang="en" xmlns="http://www.w3.org/1999/xhtml">
            <HEAD>
                <meta charset="utf-8" />
                <TITLE>{}</TITLE>
                <style>
                    a:link,a:visited {
                    color: Blue;
                    background-color: White;
                    text-decoration: underline;
                    target-new: none;
                    }
                    a:hover {
                    color: Blue;
                    background-color: Yellow;
                    text-decoration: underline;
                    target-new: none;
                    }
                </style>
            </HEAD>
            <BODY>
                <div class="topnav">
                    <a class="active" href="/">Home</a>
                        <a href="/login">Login</a>
                        <a href="/officers">Officers</a>
                        <a href="/officers_only">Officers only</a>
                        <a href="/moderartion">Moderation</a>
                </div>"""

HTML_FOOT = """</BODY></HTML>"""


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
        return redirect(url_for(".home"))

    @app.errorhandler(Unauthorized)
    async def redirect_unauthorized(e):
        return redirect(url_for("login"))

    @app.route("/me/")
    @requires_authorization
    async def _me():
        user = await discord.fetch_user()
        return f"""{HTML_HEAD.format(user.name)}
            <img src='{user.avatar_url}' />
            {HTML_FOOT}"""

    @app.route("/")
    async def home():
        content = f"""{HTML_HEAD.format('Welcome to the LPD!')}
            Welcome to the home page.
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
                        </tr>"""
        content = f"""{content}
                    </table>{HTML_FOOT}"""

        return content

    @app.route("/officers_only")
    @requires_authorization
    async def _officers_page():
        user = await discord.fetch_user()

        if user.id not in bot.officer_manager.all_officer_ids:
            content = f"""{htmL_HEAD.format('This page is restricted to LPD Officers only')}
            Sorry, this page is restricted to Officers of the LPD only.
            {HTML_FOOT}"""

            return content

        content = f"""{HTML_HEAD.format('LPD Officers only')}
            This page is for LPD Officers only. It looks like you're an officer, so welcome!
            {HTML_FOOT}"""

        return content

    @app.route("/moderation")
    @requires_authorization
    async def _moderation_page():
        user = await discord.fetch_user()
        officer = bot.officer_manager.get_officer(user.id)
        if not officer.is_white_shirt():
            content = f"""{HTML_HEAD.format('This page is for LPD White Shirts only.')}
                Sorry, you're not staff.
                {HTML_FOOT}"""

            return content
        content = f"""{HTML_HEAD.format('LPD Moderator Portal')}
            <h1 style="color: #4485b8;">LPD Moderator portal</h1>
            <p><span style="color: #000000;"><b>This is a test page for LPD Moderators only.</b></span></p>
            {HTML_FOOT}"""

        return content