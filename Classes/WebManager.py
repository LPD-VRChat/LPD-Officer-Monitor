import asyncio
import nest_asyncio

nest_asyncio.apply()

from sanic import Sanic
from sanic.response import json, html
from Classes/OfficerManager import build_officer_list

app = Sanic(name="LPD_Officer_Monitor")


class WebManager:
    def __init__(self, bot):

        self.bot = bot

    @classmethod
    async def start(cls, bot, host="0.0.0.0", port=8080):

        instance = cls(bot)
        instance.app = app
        instance.host = host
        instance.port = port
        await app.create_server(host=host, port=port, return_asyncio_server=True)

    @app.route("/")
    async def testpage(request):
        content = """<!DOCTYPE html>
            <html lang="en" xmlns="http://www.w3.org/1999/xhtml">
            <head>
                <meta charset="utf-8" />
                <title></title>
            </head>
            <body>
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

    @app.route("/officers")
    async def display_officers(request):
        content = build_officer_list()
        return html(content)