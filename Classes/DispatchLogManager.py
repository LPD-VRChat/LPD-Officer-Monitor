import asyncio
from nest_asyncio import apply

apply()

from discord import Webhook, AsyncWebhookAdapter
import aiohttp


class DispatchLogManager:
    def __init__(self, bot):

        self.bot = bot
        for _channel in bot.officer_manager.all_monitored_channels:
            channel = bot.officer_manager.guild.get_channel(_channel)
            if channel.name.lower() == "dispatch-log":
                self.dispatch_log = channel
                break

    @classmethod
    async def start(cls, bot, dispatch_webhook_url):
        instance = cls(bot)

        async with aiohttp.ClientSession() as session:
            instance.webhook = Webhook.from_url(
                dispatch_webhook_url, adapter=AsyncWebhookAdapter(session)
            )

        return instance

    async def create(self, squad_id, backup_type, world, situation):
        """Used to create an entry in #dispatch-log. Pass squad_id as int, backup type [SLRT, LMT, Patrol], world as str, situation as text."""

        backup_emoji = next(
            (x for x in self.bot.officer_manager.guild.emojis if x.name == backup_type),
            next(
                (
                    x
                    for x in self.bot.officer_manager.guild.emojis
                    if x.name == "LPD_Logo"
                ),
                "",
            ),
        )
        send_message = f"Required Backup: {backup_type} {backup_emoji}\n\nWorld: {world}\n\nSituation: {situation}\n\nSquad: {self.bot.officer_manager.guild.get_channel(squad_id).name}\n\nStatus: In-progress\n----------------------------------------"
        # message = await self.dispatch_log.send(send_message)

        await self.webhook.send("Hello World", username="Foo")

        await self.bot.sql.request(
            "INSERT INTO DispatchLog (message_id, backup_type, squad_id, world, situation, complete) VALUES (%s, %s, %s, %s, %s, %s)",
            (message.id, backup_type, squad_id, world, situation, False),
        )

        return message.id

    async def complete(self, message_id):
        """Used to edit an existing message. Pass message_id obtained from get. Returns False if no message found."""
        _entry = await self.bot.sql.request(
            "SELECT backup_type, squad_id, world, situation FROM DispatchLog WHERE message_id = %s",
            (message_id),
        )
        entry = _entry[0]
        backup_type = entry[0]
        squad_id = int(entry[1])
        world = entry[2]
        situation = entry[3]

        backup_emoji = next(
            (x for x in self.bot.officer_manager.guild.emojis if x.name == backup_type),
            next(
                (
                    x
                    for x in self.bot.officer_manager.guild.emojis
                    if x.name == "LPD_Logo"
                ),
                "",
            ),
        )
        send_message = f"Required Backup: {backup_type} {backup_emoji}\n\nWorld: {world}\n\nSituation: {situation}\n\nSquad: {self.bot.officer_manager.guild.get_channel(squad_id).name}\n\nStatus: Resolved\n----------------------------------------"

        message = await self.dispatch_log.fetch_message(message_id)
        if not message:
            return False

        await message.edit(content=send_message)
        await self.bot.sql.request(
            "REPLACE INTO DispatchLog (message_id, backup_type, squad_id, world, situation, complete) VALUES (%s, %s, %s, %s, %s, %s)",
            (message.id, backup_type, squad_id, world, situation, True),
        )

        return True

    async def get(
        self,
        backup_type=None,
        squad_id=None,
        world=None,
        situation=None,
        complete=False,
    ):
        entries = await self.bot.sql.request(
            "SELECT * FROM DispatchLog WHERE complete = %s", (complete)
        )

        results = {}
        for entry in entries:
            if (
                (backup_type is None or backup_type == entry[1])
                and (squad_id is None or squad_id == entry[2])
                and (world is None or world == entry[3])
                and (situation is None or situation == entry[4])
            ):
                squad_name = self.bot.officer_manager.guild.get_channel(
                    int(entry[2])
                ).name
                results[entry[0]] = {
                    "backup_type": entry[1],
                    "squad_id": int(entry[2]),
                    "squad_name": squad_name,
                    "world": entry[3],
                    "situation": entry[4],
                    "complete": entry[5],
                    "time": entry[6],
                }

        return results
