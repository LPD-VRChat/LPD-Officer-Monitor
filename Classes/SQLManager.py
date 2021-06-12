# ====================
# Imports
# ====================

# Standard
import asyncio
from typing import List, Union

# Community
import aiomysql
from pymysql import err as mysql_errors
import CustomTyping.modified_bot as mb


class SQLManager:
    def __init__(self, db_pool, bot: mb.Bot):
        self.bot = bot
        self.db_pool = db_pool

    @classmethod
    async def start(cls, bot: mb.Bot, db_password: str):

        # Setup database
        try:
            db_pool = await aiomysql.create_pool(
                host=bot.settings["DB_host"],
                port=3306,
                user=bot.settings["DB_user"],
                password=db_password,
                db=bot.settings["DB_name"],
                loop=asyncio.get_event_loop(),
                autocommit=True,
                unix_socket=bot.settings["DB_socket"],
            )
        except (KeyError, mysql_errors.OperationalError):
            db_pool = await aiomysql.create_pool(
                host=bot.settings["DB_host"],
                port=3306,
                user=bot.settings["DB_user"],
                password=db_password,
                db=bot.settings["DB_name"],
                loop=asyncio.get_event_loop(),
                autocommit=True,
            )

        instance = cls(db_pool, bot)

        # Set the time zone for the session to UTC as an extra measure of safety.
        await instance.request("SET time_zone = '+0:00';")

        return instance

    async def request(self, query: str, args=None) -> Union[List, None]:
        """Send a SQL request to the database.

        Usage: self.bot.sql.request(SQL_STRING)
               self.bot.sql.request(SQL_STRING, args=Tuple(variable for every %s))

        Use this function instead of officer_manager.send_db_request
        """

        async with self.db_pool.acquire() as conn:
            cur = await conn.cursor()

            await cur.execute(query, args)
            result = await cur.fetchall()

            await cur.close()

        try:
            if len(result) == 1 and len(result[0]) == 1 and result[0][0] == None:
                return None
        except IndexError:
            return None

        return result
