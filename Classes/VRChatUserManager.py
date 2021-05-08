# Standard
import csv
from typing import Optional, List, Mapping

# Community
import discord
from discord.ext import commands

#Mine
import CustomTyping.modified_bot as mb

class VRChatUserManager:
    """This class handles interaction with the user storage CSV file."""

    def __init__(self, bot: mb.Bot):
        self.bot = bot
        self.all_users: List[List] = []

    @classmethod
    async def start(cls, bot: mb.Bot):
        instance = cls(bot)
        await instance.update_cache()
        return instance

    def get_vrc_by_discord(self, discord_id: int):
        for user in self.all_users:
            if user[0] == discord_id:
                return user[1]
        return None

    def get_discord_by_vrc(self, vrchat_name: str):
        for user in self.all_users:
            if user[1] == vrchat_name:
                return user[0]
        return None

    def vrc_name_format(self, string: str) -> str:

        # Replace the characters VRChat replaces
        string = (
            string.replace("@", "＠")
            .replace("#", "＃")
            .replace("$", "＄")
            .replace("%", "％")
            .replace("&", "＆")
            .replace("=", "＝")
            .replace("+", "＋")
            .replace("/", "⁄")
            .replace("\\", "＼")
            .replace(";", ";")
            .replace(":", "˸")
            .replace(",", "‚")
            .replace("?", "？")
            .replace("!", "ǃ")
            .replace('"', "＂")
            .replace("<", "≺")
            .replace(">", "≻")
            .replace(".", "․")
            .replace("^", "＾")
            .replace("{", "｛")
            .replace("}", "｝")
            .replace("[", "［")
            .replace("]", "］")
            .replace("(", "（")
            .replace(")", "）")
            .replace("|", "｜")
            .replace("*", "∗")
        )

        return string

    async def add_user(self, discord_id: int, vrchat_name: str, skip_format_name: Optional[bool] = False):
        await self.remove_user(discord_id)

        # Format the name with modifications VRChat does
        if not skip_format_name:
            vrchat_name = self.vrc_name_format(vrchat_name)

        # Add to the cache
        self.all_users.append([discord_id, vrchat_name])

        # Add to the permanent DB
        await self.bot.sql.request(
            """
            INSERT INTO 
                VRChatNames(officer_id, vrc_name)
            VALUES
                (%s, %s);
            """,
            (discord_id, vrchat_name),
        )

    async def remove_user(self, discord_id: int):

        # Remove from the cache
        self.all_users = [x for x in self.all_users if x[0] != discord_id]

        # Remove from the permanent DB
        await self.bot.sql.request(
            "DELETE FROM VRChatNames WHERE officer_id = %s", (discord_id)
        )

    async def update_cache(self):
        db_result = await self.bot.sql.request(
            "SELECT officer_id, vrc_name FROM VRChatNames", ()
        )

        self.all_users = []

        if db_result == None:
            return
        for line in db_result:
            self.all_users.append(list(line))
