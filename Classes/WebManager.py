import asyncio
import nest_asyncio

nest_asyncio.apply()

from sanic import Sanic
from sanic.response import json, html

app = Sanic(name="LPD_Officer_Monitor")


class WebManager:
    def __init__(self, bot):

        self.bot = bot

    @classmethod
    async def start(cls, Bot, host="0.0.0.0", port=8080):
        global bot
        bot = Bot
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
                <title>testpage</title>
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
                <a href="/officers">Table of All Officers</a><br><br>The following are test objects that do nothing<br>
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