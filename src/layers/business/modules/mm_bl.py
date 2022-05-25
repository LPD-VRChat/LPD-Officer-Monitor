"""
Member Management Business Layer

Adds/Removes members from the database as they join/leave the LPD.
"""

# Standard
import asyncio
from dataclasses import dataclass
import datetime as dt
import logging
from typing import Dict

# Community
import discord
from discord.ext import commands

# Custom
import settings
from src.layers.business.extra_functions import is_lpd_member, now, get_guild
from src.layers.storage.models import Officer
from src.layers.business.base_bl import (
    DiscordListenerMixin,
    EventSenderMixin,
    bl_listen,
)

log = logging.getLogger("lpd-officer-monitor")

# TODO: Try to make this more concise with a single class decorator
class MemberManagementEvent:
    @dataclass
    class MemberJoined:
        officer: Officer
        member: discord.Member

    @dataclass
    class MemberJoinedAfterMaxWait:
        officer: Officer
        member: discord.Member

    @dataclass
    class MemberLeft:
        member: discord.Member


MEMBER_MANAGEMENT_EVENT_TYPE = (
    MemberManagementEvent.MemberJoined
    | MemberManagementEvent.MemberLeft
    | MemberManagementEvent.MemberJoinedAfterMaxWait
)


class MemberManagementBL(
    DiscordListenerMixin, EventSenderMixin[MEMBER_MANAGEMENT_EVENT_TYPE]
):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

        # Initialize the cache
        loop = asyncio.get_event_loop()
        all_active_officers = loop.run_until_complete(
            Officer.objects.all(deleted_at=None)
        )
        self._lpd_members: Dict[int, Officer] = {o.id: o for o in all_active_officers}

    # Add/remove members on discord changes
    async def member_joined_LPD(self, member: discord.Member) -> None:
        # Get or create the officer
        officer = await Officer.objects.get_or_none(id=member.id)

        # Create or update the officer in the database
        if officer is not None:
            last_allowed_return_time = now() - dt.timedelta(days=7)
            if officer.deleted_at and officer.deleted_at > last_allowed_return_time:
                # Reset the needed data on the officer
                officer.started_monitoring = now()
                officer.vrchat_name = ""
                officer.vrchat_id = ""
                officer.deleted_at = None
                await officer.update()

                # Let all subscribers know that they may need to remove any data
                self._notify_all(
                    MemberManagementEvent.MemberJoinedAfterMaxWait(officer, member)
                )
            else:
                # The officer can keep their data as they joined back within the grace period
                self._notify_all(MemberManagementEvent.MemberJoined(officer, member))
        else:
            # A new officer needs to be created
            officer = Officer(
                id=member.id, started_monitoring=now(), vrchat_name="", vrchat_id=""
            )
            await officer.save()
            self._notify_all(MemberManagementEvent.MemberJoined(officer, member))

        # Add the officer to the cache
        self._lpd_members[officer.id] = officer

        # Log the event
        log.info(
            f"{member.display_name} ({member.name}#{member.discriminator}) has been added to the database."
        )

    async def member_left_LPD(self, member: discord.Member) -> None:
        # Store when they were removed
        officer = await Officer.objects.get(id=member.id)
        officer.deleted_at = now()
        await officer.update()

        # Remove them from the cache
        del self._lpd_members[officer.id]

        # Let others know
        log.info(
            f"{member.display_name} ({member.name}#{member.discriminator}) has been removed from the LPD."
        )
        self._notify_all(MemberManagementEvent.MemberLeft(member))

    @bl_listen()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member,
    ) -> None:
        officer_before = before.id in self._lpd_members
        officer_after = is_lpd_member(after)

        match (officer_before, officer_after):
            case (True, True):
                # Nothing happened to an LPD Officer
                log.debug(
                    "member_join_leave - LPD officer did not do anything interesting"
                )
            case (False, False):
                # Nothing happened to a regular member
                log.debug(
                    "member_join_leave - Regular member did not do anything interesting"
                )
            case (False, True):
                # Member has joined the LPD
                await self.member_joined_LPD(after)
            case (True, False):
                # Member has left the LPD
                await self.member_left_LPD(after)

    @bl_listen()
    async def on_member_remove(self, member: discord.Member) -> None:
        await self.member_left_LPD(member)

    # Verify members at startup
    @bl_listen("on_ready")
    async def find_missing_officers(self) -> None:
        guild = get_guild(self.bot)
        loop = asyncio.get_event_loop()
        tasks = []

        # Find missing officers
        for member in guild.members:
            if is_lpd_member(member) and member.id not in self._lpd_members:
                # The member has LPD roles but wasn't in the database.
                log.warning(
                    f"{member.id} ({member.display_name}) was in the LPD but not in the database."
                )
                tasks.append(loop.create_task(self.member_joined_LPD(member)))

        # Find extra officers
        for officer in list(self._lpd_members.values()):
            member = guild.get_member(officer.id)
            if not is_lpd_member(member):
                # The member doesn't have LPD roles but was still in the database
                log.warning(f"{officer.id} was in the database but not in the LPD.")
                tasks.append(loop.create_task(self.member_left_LPD(member)))

        await asyncio.gather(*tasks)
