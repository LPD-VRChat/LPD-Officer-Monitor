import asyncio
import nest_asyncio

from Classes.errors import MemberNotFoundError

nest_asyncio.apply()


class Event_:
    def __init__(self, user_id, bot):
        self.bot = bot
        self.host = user_id
        self.host = bot.officer_manager.get_officer(user_id)
