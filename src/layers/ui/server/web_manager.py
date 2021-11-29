import settings
import keys

import asyncio
import nest_asyncio

import time
from datetime import datetime, timedelta
import re
import signal
import moviepy.editor as mp
import numpy as np
from array2gif import write_gif
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

app = Quart("LPD Officer Monitor", static_folder="Webapp/")
app.config["DISCORD"] = None
log = logging.getLogger("lpd-officer-monitor")


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
    # fmt: off
    dataset[0][0] = _white_value_RGB if officer.is_cadet else _black_value_RGB
    dataset[0][1] = _white_value_RGB if officer.is_white_shirt else _black_value_RGB
    # Since we return the blank template if not officer, then we return true here always
    dataset[0][2] = _white_value_RGB
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
    dataset[3][3] = _white_value_RGB if officer.is_media_production else _black_value_RGB
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

    dataset[5][0] = _white_value_RGB if officer.is_programming_team else _black_value_RGB
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

    ############### WARNING: We can't reliably check this value in an 8x8
    dataset[7][0] = _red_value_RGB
    dataset[7][1] = _black_value_RGB
    dataset[7][2] = _black_value_RGB
    dataset[7][3] = _black_value_RGB
    dataset[7][4] = _black_value_RGB
    dataset[7][5] = _black_value_RGB
    dataset[7][6] = _black_value_RGB
    dataset[7][7] = _black_value_RGB
    # fmt: on
    # Save the GIF
    write_gif(dataset, real_filename)


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

        app.secret_key = keys.WEB_SECRET_KEY

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
        await asyncio.sleep(1)
        if self.__stop_the_server__:
            self.__stop_the_server__ = False
            return
        await self.shutdown_trigger()  # TODO: This will cause a stack overflow when run for a few thousands or millions of seconds

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
    async def favicon():
        return await send_file("/favicon.ico")

    @app.route("/")
    async def app_home():
        return await send_file("src/layers/ui/web_app/index.html")

    @app.route("/main.js")
    async def main_js():
        return await send_file("src/layers/ui/web_app/main.js")
