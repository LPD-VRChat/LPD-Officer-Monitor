# Standard
import csv

# Community
import discord
from discord.ext import commands

class VRChatUserManager():
    """This class handles interaction with the user storage CSV file."""

    def __init__(self, bot):
        self.bot = bot
        self.all_users = []
    
    @classmethod
    async def start(cls, bot):
        instance = cls(bot)
        await instance.update_cache()
        return instance
    
    def get_vrc_by_discord(self, discord_id):
        for user in self.all_users:
            if user[0] == discord_id:
                return user[1]
        return None

    def get_discord_by_vrc(self, vrchat_name):
        for user in self.all_users:
            if user[1] == vrchat_name:
                return user[0]
        return None

    async def add_user(self, discord_id, vrchat_name):
        await self.remove_user(discord_id)

        # Add to the cache
        self.all_users.append([discord_id, vrchat_name])

        # Add to the permanent DB
        await self.bot.officer_manager.send_db_request(
            """
            INSERT INTO 
                VRChatNames(officer_id, vrc_name)
            VALUES
                (%s, %s);
            """,
            (discord_id, vrchat_name)
        )
    
    async def remove_user(self, discord_id):

        # Remove from the cache
        self.all_users = [x for x in self.all_users if x[0] != discord_id]
        
        # Remove from the permanent DB
        await self.bot.officer_manager.send_db_request(
            "DELETE FROM VRChatNames WHERE officer_id = %s",
            (discord_id)
        )

    async def update_cache(self):
        db_result = await self.bot.officer_manager.send_db_request(
            "SELECT officer_id, vrc_name FROM VRChatNames", ()
        )
        
        self.all_users = []

        print(f"DB_result: {repr(db_result)}")
        if db_result == None: return
        for line in db_result:
            print(f"Line: {repr(line)}")
            self.all_users.append(list(line))
    