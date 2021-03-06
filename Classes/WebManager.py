import asyncio
import nest_asyncio

nest_asyncio.apply()
from quart import Quart, redirect, url_for
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized

app = Quart("LPD Officer Monitor")


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
    async def start(cls, Bot, host="0.0.0.0", port=8080, id=None, secret=None):
        global bot
        bot = Bot
        instance = cls(bot)

        app.secret_key = b"random bytes representing quart secret key"

        app.config["DISCORD_CLIENT_ID"] = id  # Discord client ID.
        app.config["DISCORD_CLIENT_SECRET"] = secret  # Discord client secret.
        app.config[
            "DISCORD_REDIRECT_URI"
        ] = "http://devbox.lolipd.com/officers"  # URL to your callback endpoint.
        app.config["DISCORD_BOT_TOKEN"] = ""  # Required to access BOT resources.

        discord = DiscordOAuth2Session(app)

        #   endpoint_path = "https://discord.com/api/oauth2/authorize?client_id=764230749992779806&redirect_uri=http%3A%2F%2Fdevbox.lolipd.com%2Fofficers&response_type=code&scope=identify%20email"

        app.run()

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

    @app.route("/")
    async def home():
        content = """<!DOCTYPE html>
            <html lang="en" xmlns="http://www.w3.org/1999/xhtml">
            <head>
                <meta charset="utf-8" />
                <title>Welcome to the Loli Police Department!</title>
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
            </head>
            <body>
                <a href="/officers">Table of All Officers</a><br><br>
                <a href="/login">Login</a><br><br>
                The following are test objects that do nothing<br>
                <input type="text" name="fname"><br>
                <select>
                    <option value="volvo">Volvo</option>
                    <option value="saab">Saab</option>
                    <option value="mercedes">Mercedes</option>
                    <option value="audi">Audi</option>
                </select><br>
                <input type="submit" value="Submit"><br>
                <input type="color" value="#ff0000"><br>
                <input type="date" value="2017-06-01" min="1980-04-01" max="2099-04-30"><br>
                <input type="radio" name="gender" value="male"> Male<br>
            </body>
            </html>"""
        return content

    @app.route("/login/")
    async def login():
        return await discord.create_session()

    @app.route("/officers")
    @requires_authorization()
    async def display_officers():

        content = f"""<!DOCTYPE html>
            <html lang="en" xmlns="http://www.w3.org/1999/xhtml">
            <head>
                <meta charset="utf-8" />
                <title>List of all officers</title>
            </head>
            <body>{user}</br><br>
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
                    </table></body></html>"""

        return content