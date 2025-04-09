"""
Member Management Business Layer

Adds/Removes members from the database as they join/leave the LPD.
"""

# Standard
import asyncio
from dataclasses import dataclass
import datetime as dt
import logging
from typing import Dict, Optional

# Community
import discord
from discord.ext import commands, tasks
from thefuzz.fuzz import partial_token_sort_ratio

# Custom
import settings
from src.layers.business.extra_functions import (
    is_lpd_member,
    now,
    get_guild,
    timedelta_to_nice_string,
)
from src.layers.storage.models import Officer
from src.layers.business.base_bl import (
    DiscordListenerMixin,
    EventSenderMixin,
    bl_listen,
)
from src.layers.business.modules.pt_bl import PatrolTimeBL

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
        member_id: int
        member: Optional[discord.Member]


MEMBER_MANAGEMENT_EVENT_TYPE = (
    MemberManagementEvent.MemberJoined
    | MemberManagementEvent.MemberLeft
    | MemberManagementEvent.MemberJoinedAfterMaxWait
)


class MemberManagementBL(
    DiscordListenerMixin, EventSenderMixin[MEMBER_MANAGEMENT_EVENT_TYPE]
):
    def __init__(
        self,
        bot: commands.Bot,
        pt_bl: PatrolTimeBL,
    ) -> None:
        self.bot = bot
        super().__init__()
        self.pt_bl = pt_bl

        # Initialize the cache
        loop = asyncio.get_event_loop()
        all_active_officers = loop.run_until_complete(
            Officer.objects.all(deleted_at=None)
        )
        self._lpd_members: Dict[int, Officer] = {o.id: o for o in all_active_officers}
        self.filming_crew = asyncio.Queue()

    @bl_listen("on_ready")
    async def on_ready(self):
        if not self.filming_crew_cleanup_task.is_running():
            self.filming_crew_cleanup_task.start()
        film_crew_role = self.bot.get_guild(settings.SERVER_ID).get_role(
            settings.FILMING_CREW_ROLE
        )
        if film_crew_role:
            for m in film_crew_role.members:
                self.filming_crew.put_nowait(m)

    @bl_listen()
    async def on_unload(self):
        self.filming_crew_cleanup_task.cancel()

    # Add/remove members on discord changes
    async def member_joined_LPD(self, member: discord.Member) -> None:
        # Get or create the officer
        officer = await Officer.objects.get_or_none(id=member.id)

        # Create or update the officer in the database
        if officer is not None:
            last_allowed_return_time = now() - dt.timedelta(days=7)
            if officer.deleted_at and officer.deleted_at < last_allowed_return_time:
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
                officer.deleted_at = None
                await officer.update()
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
        log.info(f"{member.display_name} ({member.id}) has been added to the database.")

    async def member_left_LPD(
        self, member_id: int, member: Optional[discord.Member]
    ) -> None:
        # added id because of find_missing_officers
        # no member when already left

        # Store when they were removed
        officer = await Officer.objects.get(id=member_id)
        officer.deleted_at = now()
        await officer.update()

        # Remove them from the cache
        del self._lpd_members[officer.id]

        # Let others know
        if member:
            log.info(
                f"{member.display_name} ({member.id}) has been removed from the LPD.\n"
                "roles= `" + ",".join([str(role.id) for role in member.roles]) + "`"
            )
        else:
            log.info(
                f"vrc:`{officer.vrchat_name}`({officer.vrchat_id})[discordId:{member_id}] has been removed from the LPD."
            )
        self._notify_all(MemberManagementEvent.MemberLeft(member_id, member))

    @bl_listen()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member,
    ) -> None:
        # listen to roles only in LPD server
        # if needed for other server, listen to same event in another module
        if not before.guild.id == settings.SERVER_ID:
            return
        officer_before = before.id in self._lpd_members
        officer_after = is_lpd_member(after)

        match (officer_before, officer_after):
            case (True, True):
                # Nothing happened to an LPD Officer
                if settings.CONFIG_LOADED == "dev":
                    log.debug(
                        "member_join_leave - LPD officer did not do anything interesting"
                    )
            case (False, False):
                # Nothing happened to a regular member
                if settings.CONFIG_LOADED == "dev":
                    log.debug(
                        "member_join_leave - Regular member did not do anything interesting"
                    )
            case (False, True):
                # Member has joined the LPD
                await self.member_joined_LPD(after)
            case (True, False):
                # Member has left the LPD
                await self.member_left_LPD(after.id, after)

        if (
            before.get_role(settings.FILMING_CREW_ROLE) == None
            and after.get_role(settings.FILMING_CREW_ROLE) != None
        ):
            await self.filming_crew.put(after)

    @bl_listen()
    async def on_member_remove(self, member: discord.Member) -> None:
        if is_lpd_member(member) and member.guild.id == settings.SERVER_ID:
            await self.member_left_LPD(member.id, member)

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
                    f"{member.display_name} ({member.id}) was in the LPD but not in the database."
                )
                tasks.append(loop.create_task(self.member_joined_LPD(member)))

        # Find extra officers
        for officer in list(self._lpd_members.values()):
            member = guild.get_member(officer.id)
            if not is_lpd_member(member):
                # The member doesn't have LPD roles but was still in the database
                # log.warning(f"{officer.id} was in the database but not in the LPD.")
                tasks.append(loop.create_task(self.member_left_LPD(officer.id, member)))

        await asyncio.gather(*tasks)

    async def get_officer_vrcname_from_id(self, id: int) -> str:
        of = await Officer.objects.get(id=id)
        return of.vrchat_name

    @tasks.loop(minutes=10.0)
    async def filming_crew_cleanup_task(self):
        if self.filming_crew.empty():
            return
        while True:
            try:
                crew = self.filming_crew.get_nowait()
            except asyncio.QueueEmpty:
                return
            try:
                await crew.remove_roles(
                    discord.Object(settings.FILMING_CREW_ROLE),
                    reason="Film crew cleanup",
                )
            except:
                log.exception(f"filming_crew_cleanup_task failed for {crew.id=}")
            self.filming_crew.task_done()

    async def member_dump(self, id: int) -> str:
        of = await Officer.objects.get(id=id)
        r = f"discordid={of.id} <@{of.id}>\n"
        r += f"{"started:"+of.started_monitoring.isoformat() if of.started_monitoring else 'invalid_start'}\n"
        r += f"{"left:"+of.deleted_at.isoformat() if of.deleted_at else 'active'}\n"
        r += f"vrchat_name=`{of.vrchat_name}`\n"
        r += f"vrchat_id=`{of.vrchat_id}`\n"
        to_dt = dt.datetime.now(dt.timezone.utc)
        from28_dt = to_dt - dt.timedelta(days=28)
        from90_dt = to_dt - dt.timedelta(days=90)
        timeDelta28 = await self.pt_bl.get_patrol_time(
            id, from_dt=from28_dt, to_dt=to_dt
        )
        timeDelta90 = await self.pt_bl.get_patrol_time(
            id, from_dt=from90_dt, to_dt=to_dt
        )
        r += f"Patrol 28 days: {timedelta_to_nice_string(timeDelta28)}\n"
        r += f"Patrol 90 days: {timedelta_to_nice_string(timeDelta90)}\n"
        return r

    async def expensive_lookup(
        self,
        search: str,
    ) -> str:
        results = []
        suggestions = set()

        async for officer in Officer.objects.iterate():
            if partial_token_sort_ratio(search, officer.vrchat_name) > 80:
                suggestions.add(officer.id)
                results.append(
                    f"vrchat name partial match id=`{officer.id}` vrcname=`{officer.vrchat_name}`"
                )
        for member in self.bot.get_guild(settings.SERVER_ID).members:
            if (
                partial_token_sort_ratio(search, member.name) > 80
                or partial_token_sort_ratio(search, member.display_name) > 80
            ):
                suggestions.add(member.id)
                results.append(
                    f"discord name partial match id=`{member.id}` name=`{member.name}` display_name=`{member.display_name}`"
                )

        return "\n".join(results)

    async def member_lookup(
        self,
        search: str,
    ) -> str:
        result = ""
        found = 0
        discord_id = None
        try:
            discord_id = int(search)
        except ValueError:
            pass
        dumped = set()
        if discord_id is not None:
            result += "# discord ID match\n" + await self.member_dump(discord_id) + "\n"
            found += 1
            dumped.add(discord_id)

        of = await Officer.objects.get_or_none(vrchat_name=search)
        if of is not None:
            if of.id not in dumped:
                result += (
                    "# vrchat name exact match\n" + await self.member_dump(of.id) + "\n"
                )
                found += 1
                dumped.add(of.id)

        of = await Officer.objects.get_or_none(vrchat_id=search)
        if of is not None:
            if of.id not in dumped:
                result += "# vrchat ID match\n" + await self.member_dump(of.id) + "\n"
                found += 1
                dumped.add(of.id)

        for member in self.bot.get_guild(settings.SERVER_ID).members:
            if member.name == search:
                if member.id not in dumped:
                    result += (
                        "# discord name exact match\n"
                        + await self.member_dump(member.id)
                        + "\n"
                    )
                    found += 1
                    dumped.add(member.id)
            if member.display_name == search:
                if member.id not in dumped:
                    result += (
                        "# discord display name exact match\n"
                        + await self.member_dump(member.id)
                        + "\n"
                    )
                    found += 1
                    dumped.add(member.id)

        if found == 0:
            result = "# No exact match found\n"
            er = await self.expensive_lookup(search)
            if len(er) == 0:
                result += "# No suggestions found\n"
            else:
                result += " Suggestions: (re run the command using the id)\n" + er

        return result
