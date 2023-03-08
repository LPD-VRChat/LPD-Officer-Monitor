import settings

import asyncio
import nest_asyncio

import time
from datetime import datetime, timedelta
import re
import signal
from urllib.parse import unquote_plus as dec
from os import path, stat
from collections import OrderedDict
import json
import logging

from quart import (
    Quart,
    redirect,
    url_for,
    request,
    send_file,
    render_template,
    jsonify,
    send_from_directory,
)
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
from hypercorn.asyncio import serve
from hypercorn.config import Config

nest_asyncio.apply()

# TODO: Somehow move these into the WebManager class to minimize global variables, I'm thinking we can use just app.route directly in main, but I'm not sure if thats the best solution
app = Quart("LPD Officer Monitor", static_folder="Webapp/")
app.config["DISCORD"] = None

log = logging.getLogger("lpd-officer-monitor")


class WebManager:
    def __init__(self, bot, app, config):

        self.bot = bot
        self.app = app
        self.config = config
        self.loop = asyncio.get_event_loop()
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

        app.secret_key = settings.WEB_SECRET_KEY

        app.config["DISCORD_CLIENT_ID"] = id
        app.config["DISCORD_CLIENT_SECRET"] = secret
        app.config["DISCORD_BOT_TOKEN"] = token
        app.config["DISCORD_REDIRECT_URI"] = callback
        app.config["SERVER_NAMES"] = ["devbox.lolipd.com", "www.lolipd.com"]
        app.config["SCOPES"] = ["identify"]
        app.config["BOT"] = _Bot
        app.config["TEMPLATES_AUTO_RELOAD"] = True

        _Discord = DiscordOAuth2Session(app)
        app.config["DISCORD"] = _Discord

        config = Config()

        if path.exists(certfile) and path.exists(keyfile):
            config.certfile = certfile
            config.keyfile = keyfile

        else:  # TODO: This overrides a port configuration in settings
            port = 80
            log.warning("No SSL cert or key found, using HTTP!")

        config.bind = [f"{host}:{port}"]
        config.worker_class = ["asyncio"]
        config.server_names = app.config["SERVER_NAMES"]
        config.accesslog = "/var/log/LPD-Officer-Monitor/access.log"
        config.errorlog = "/var/log/LPD-Officer-Monitor/error.log"

        instance = cls(_Bot, app, config)
        return instance

    async def shutdown_trigger(self):
        while True:
            await asyncio.sleep(1)
            if self.__stop_the_server__:
                self.__stop_the_server__ = False
                return

    async def start(self):
        self.task = self.loop.create_task(
            serve(self.app, self.config, shutdown_trigger=self.shutdown_trigger)
        )

    async def stop(self):
        log.warning("WebManager has been stopped")
        self.__stop_the_server__ = True

    async def restart(self, wait_time=5):
        log.info("Restarting WebManager...")
        self.__stop_the_server__ = True
        await asyncio.sleep(wait_time)
        await self.start()

    async def reload(self):
        pass

    @app.route("/login/")
    async def login(self):
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        return await discord.create_session(scope=app.config["SCOPES"])

    @app.route("/logout/")
    async def logout(self):
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        await discord.close_session()
        return redirect(url_for("home"))

    @app.route("/callback/")
    async def callback(self):
        discord = app.config["DISCORD"]
        bot = app.config["BOT"]

        try:
            await discord.callback()
        except:
            pass
        user = await discord.fetch_user()
        log.info(f"{user.name} logged in")
        return redirect(url_for(".home"))

    @app.errorhandler(Unauthorized)
    async def redirect_unauthorized(error):
        return redirect(url_for("login"))

    @app.route("/favicon.ico")
    async def favicon(self):
        return await send_file("/favicon.ico")

    @app.route("/")
    async def app_home(self):
        return await send_file("src/layers/ui/web_app/index.html")

    @app.route("/main.js")
    async def main_js(self):
        return await send_file("src/layers/ui/web_app/main.js")
