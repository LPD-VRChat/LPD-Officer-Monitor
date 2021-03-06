import asyncio
import nest_asyncio

nest_asyncio.apply()

import aiohttp
from collections import defaultdict
from sanic import Sanic
from sanic.response import json, html, text, HTTPResponse
from sanic.request import Request
from sanic_session import InMemorySessionInterface
from sanic_oauth.blueprint import oauth_blueprint, login_required

app = Sanic(name="LPD_Officer_Monitor")
global code
code = ""


class WebManager:
    def __init__(self, bot):

        self.bot = bot

    @classmethod
    async def start(cls, Bot, host="0.0.0.0", port=8080, id=None, secret=None):
        global bot
        bot = Bot
        instance = cls(bot)

        app.blueprint(oauth_blueprint)
        app.session_interface = InMemorySessionInterface()

        instance.app = app
        instance.host = host
        instance.port = port

        app.config.OAUTH_REDIRECT_URI = "http://devbox.lolipd.com/officers"
        app.config.OAUTH_SCOPE = "email"
        app.config.OAUTH_PROVIDERS = defaultdict(dict)
        DISCORD_PROVIDER = app.config.OAUTH_PROVIDERS["discord"]
        DISCORD_PROVIDER["PROVIDER_CLASS"] = "sanic_oauth.providers.DiscordClient"
        DISCORD_PROVIDER["SCOPE"] = "identify email"
        DISCORD_PROVIDER["CLIENT_ID"] = id
        DISCORD_PROVIDER["CLIENT_SECRET"] = secret
        DISCORD_PROVIDER[
            "EMAIL_REGEX"
        ] = """\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"""
        DISCORD_PROVIDER[
            "ENDPOINT_PATH"
        ] = "https://discord.com/api/oauth2/authorize?client_id=764230749992779806&redirect_uri=http%3A%2F%2Fdevbox.lolipd.com%2Fofficers&response_type=code&scope=identify%20email"

        app.config.OAUTH_PROVIDERS["default"] = DISCORD_PROVIDER

        await app.create_server(host=host, port=port, return_asyncio_server=True)

    @app.listener("before_server_start")
    async def init_aiohttp_session(sanic_app, _loop) -> None:
        sanic_app.async_session = aiohttp.ClientSession()

    @app.listener("after_server_stop")
    async def close_aiohttp_session(sanic_app, _loop) -> None:
        await sanic_app.async_session.close()

    @app.middleware("request")
    async def add_session_to_request(request):
        # before each request initialize a session
        # using the client's request
        await request.app.session_interface.open(request)

    @app.middleware("response")
    async def save_session(request, response):
        # after each request save the session,
        # pass the response to set client cookies
        print(request)
        await request.app.session_interface.save(request, response)

    @app.route("/")
    async def home(_request) -> HTTPResponse:
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
        return html(content)

    @app.route("/login")
    @login_required()
    async def _login(_request: Request, user) -> HTTPResponse:
        content = """<!DOCTYPE html>
            <html lang="en" xmlns="http://www.w3.org/1999/xhtml">
            <head>
                <meta charset="utf-8" />
                <title>Login Redirect</title>
            </head>
            <body>Redirecting to Discord login...
            </body></html>"""
        return html(content)

    @app.route("/officers")
    # @login_required()
    async def display_officers(_request: Request) -> HTTPResponse:
        code = _request.args.get(code, "")

        if code == "":
            return html("NO")

        content = """<!DOCTYPE html>
            <html lang="en" xmlns="http://www.w3.org/1999/xhtml">
            <head>
                <meta charset="utf-8" />
                <title>List of all officers</title>
            </head>
            <body>
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

        return html(content)