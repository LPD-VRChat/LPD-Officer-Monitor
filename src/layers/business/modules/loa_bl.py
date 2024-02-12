"""
Activity Logging Business Layer

Record when officer where last active in the comunity
"""

# Standard
import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Iterable
from enum import Enum

# Community
import discord
from discord.ext import commands
import ormar

# Custom
import settings
from src.layers.business.base_bl import DiscordListenerMixin, bl_listen
from src.layers.business.extra_functions import is_lpd_member, now, get_guild
from src.layers.storage import models

log = logging.getLogger("lpd-officer-monitor")


class ActivityTypes(Enum):
    UNDEFINED = 0
    MESSAGE = 1
    DUTY = 2
    RENEWAL = 3


class MemberActivityBL(DiscordListenerMixin):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @bl_listen()
    async def on_message(self, message: discord.Message) -> None:
        if (
            not message.guild
            or message.guild.id != settings.SERVER_ID
            or message.author.bot
        ):
            return

        if not message.channel.id == settings.LEAVE_OF_ABSENCE_CHANNEL:
            return

        if not is_lpd_member(message.author):
            log.error(
                f"User `{message.author.name}`[{message.author.id}] had access to loa channel but isn't LPD member"
            )
            await message.delete()
            return

        await self.process_loa(message)

    @bl_listen()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        if payload.channel_id != settings.LEAVE_OF_ABSENCE_CHANNEL:
            return
        try:
            entry = await models.LOAEntry.objects.get(message_id=payload.message_id)
        except ormar.NoMatch:
            return

        entry.deleted_at = datetime.utcnow()
        await entry.update()
        channel: discord.TextChannel = self.bot.get_channel(payload.channel_id)
        partial_message = channel.get_partial_message(payload.message_id)
        if not settings.DRY_RUN:
            await channel.send(
                content=f"<@{entry.officer.id}> Editing an LOA is not permited. You need to create a new one",
                delete_after=30,
            )
            await partial_message.delete()

    async def process_loa(self, message: discord.Message):
        # from V2
        try:
            date_range = message.content.split(":")[0]
            date_a = date_range.split("-")[0]
            date_b = date_range.split("-")[1]
            date_start = ["", "", ""]
            date_end = ["", "", ""]
            date_start[0] = date_a.split("/")[0].strip()
            date_start[1] = date_a.split("/")[1].strip()
            date_start[2] = date_a.split("/")[2].strip()
            date_end[0] = date_b.split("/")[0].strip()
            date_end[1] = date_b.split("/")[1].strip()
            date_end[2] = date_b.split("/")[2].strip()
            reason = message.content.split(":")[1].strip()
            months = {
                "JAN": 1,
                "FEB": 2,
                "MAR": 3,
                "APR": 4,
                "MAY": 5,
                "JUN": 6,
                "JUL": 7,
                "AUG": 8,
                "SEP": 9,
                "OCT": 10,
                "NOV": 11,
                "DEC": 12,
            }

            # Ensure day is numeric
            int(date_start[0])
            int(date_end[0])

            # Ensure year is numeric
            int(date_start[2])
            int(date_end[2])

            # Get month number from dictionary
            date_start[1] = date_start[1].upper()[0:3]
            date_start[1] = months[date_start[1]]
            date_end[1] = date_end[1].upper()[0:3]
            date_end[1] = months[date_end[1]]

        except (TypeError, ValueError, KeyError, IndexError):
            # If all of that failed, let the user know with an autodeleting message
            if not settings.DRY_RUN:
                await message.channel.send(
                    message.author.mention
                    + " Please use correct formatting: 21/July/2020 - 21/August/2020: Reason.",
                    delete_after=10,
                )
                await message.delete()
            return

        date_start = [int(i) for i in date_start]
        date_end = [int(i) for i in date_end]

        if (
            date_start[1] < 1
            or date_start[1] > 12
            or date_end[1] < 1
            or date_end[1] > 12
        ):
            # If the month isn't 1-12, let the user know they dumb
            if not settings.DRY_RUN:
                await message.channel.send(
                    message.author.mention + " There are only 12 months in a year.",
                    delete_after=10,
                )
                await message.delete()
            return

        # Convert our separate data into a usable datetime
        date_start_complex = (
            str(date_start[0]) + "/" + str(date_start[1]) + "/" + str(date_start[2])
        )
        date_end_complex = (
            str(date_end[0]) + "/" + str(date_end[1]) + "/" + str(date_end[2])
        )

        try:
            date_start = datetime.strptime(date_start_complex, "%d/%m/%Y")
            date_end = datetime.strptime(date_end_complex, "%d/%m/%Y")
        except (ValueError, TypeError):
            if not settings.DRY_RUN:
                await message.channel.send(
                    message.author.mention
                    + " There was a problem with your day. Please use a valid day number.",
                    delete_after=10,
                )
                await message.delete()
            return

        if date_end > date_start + timedelta(
            weeks=+12
        ) or date_end < date_start + timedelta(weeks=+3):
            # If more than 12 week LOA, inform user
            if not settings.DRY_RUN:
                await message.channel.send(
                    message.author.mention
                    + " Leaves of Absence are limited to 3-12 weeks. For longer times, please contact a White Shirt (Lieutenant or Above).",
                    delete_after=10,
                )
                await message.delete()
            return

        # Make sure the LOA isn't over yet
        if date_end < datetime.utcnow():
            if not settings.DRY_RUN:
                await message.channel.send(
                    f"{message.author.mention} The leave of absence you supplied has already expired.",
                    delete_after=10,
                )
                await message.delete()
            return

        await self.save_loa(
            message.author.id,
            date_start,
            date_end,
            message.id,
            message.channel.id,
            reason,
        )
        await message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    async def save_loa(
        self, officer_id, date_start, date_end, request_id, channel_id, reason_message
    ):
        """
        Pass all 5 required fields to save_loa()
        If record with matching officer_id is found,
        record will be updated with new dates and reason.
        """
        try:
            prevLoa = await models.LOAEntry.objects.get(officer=officer_id)
            ch = self.bot.get_channel(prevLoa.channel_id)
            if ch and not settings.DRY_RUN:
                try:
                    await ch.delete_messages(
                        messages=[discord.Object(id=prevLoa.message_id)],
                        reason="updated LOA",
                    )
                except discord.NotFound:
                    pass
            prevLoa.deleted_at = datetime.utcnow()
            await prevLoa.update()
        except ormar.NoMatch:
            pass
        except ormar.MultipleMatches:
            log.debug(f"multiple loa ongoing for officer {officer_id}")
            prevLoa = await models.LOAEntry.objects.all(officer=officer_id)
            for l in prevLoa:
                ch = self.bot.get_channel(l.channel_id)
                if ch and not settings.DRY_RUN:
                    try:
                        await ch.delete_messages(
                            messages=[discord.Object(id=l.message_id)],
                            reason="updated LOA, multiple!!!",
                        )
                    except discord.NotFound:
                        pass
                l.deleted_at = datetime.utcnow()
                await l.update()

        await models.LOAEntry.objects.create(
            officer=officer_id,
            start=date_start,
            end=date_end,
            message_id=request_id,
            channel_id=channel_id,
            created_at=datetime.utcnow(),
            reason=reason_message,
        )

    async def list_loa(self) -> Iterable[models.LOAEntry]:
        now = date.today()
        return await models.LOAEntry.objects.filter(
            models.LOAEntry.start >= now, models.LOAEntry.deleted_at.isnull(True)
        ).all()

    async def list_renewed(self, date_from: date) -> Iterable[models.TimeRenewal]:
        return await models.TimeRenewal.objects.filter(
            models.TimeRenewal.timestamp >= date_from
        ).all()

    async def process_inactives(
        self, bellow_time: list[models.Officer], loa, renew
    ) -> list[models.Officer]:
        # lookup in dict is O^1
        loa_dict = {l.officer.id: l for l in loa}
        renew_dict = {r.officer.id: r for r in renew}

        inactive = [
            officer
            for officer in bellow_time
            if officer.id not in loa_dict and officer.id not in renew_dict
        ]
        return inactive

    async def create_renew(self, officer_id: int, origin_id: int):
        await models.TimeRenewal.objects.create(
            officer=officer_id,
            timestamp=datetime.now(),
            renewer=origin_id,
        )

    async def list_renew(self, officer_id) -> list[models.TimeRenewal]:
        return await models.TimeRenewal.objects.all(officer=officer_id)
