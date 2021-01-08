# ====================
# Imports
# ====================

# Standard
import asyncio


# Community
import aiomysql
from pymysql import err as mysql_errors

class SQLManager:
    def __init__(self, db_pool, all_officer_ids, bot):
        self.bot = bot
        self.db_pool = db_pool


    @classmethod
    async def start(cls, bot, db_password):

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

        # Fetch all the officers from the database
        try:
            async with db_pool.acquire() as conn:
                cur = await conn.cursor()
                await cur.execute("SELECT officer_id FROM Officers")
                result = await cur.fetchall()
                await cur.close()
        except Exception as error:
            print("ERROR failed to fetch officers from database:")
            print(error)
            print("Shutting down...")
            exit()

        self.all_officer_ids = (x[0] for x in result)

        return cls(
            db_pool,
            (x[0] for x in result),
            bot,
        )

    async def request(self, query, args=None):

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