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
from src.layers.storage import models
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
    MemberManagementEvent,
)
from src.layers.business.modules.pt_bl import PatrolTimeBL

log = logging.getLogger("lpd-officer-monitor")


MEMBER_MANAGEMENT_EVENT_TYPE = (
    MemberManagementEvent.MemberJoined
    | MemberManagementEvent.MemberLeft
    | MemberManagementEvent.MemberJoinedAfterMaxWait
)


class MemberManagementBL(
    DiscordListenerMixin,
    EventSenderMixin,
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
        self.role_update_blocklist = set[int]()

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
        left_reason = "unknown"
        if officer and officer.extra and "left_reason" in officer.extra:
            left_reason = officer.extra["left_reason"]

        # Create or update the officer in the database
        if officer is not None:
            last_allowed_return_time = now() - dt.timedelta(days=7)
            outside_grace_period = (
                officer.deleted_at and officer.deleted_at < last_allowed_return_time
            )
            inactive = left_reason.startswith("inactive")
            if outside_grace_period or inactive:
                log.info(
                    f"`{member.display_name}` ({member.id}) reset existing data because {left_reason=} {outside_grace_period=} {inactive=}."
                )
                # Reset the needed data on the officer
                officer.started_monitoring = now()
                officer.vrchat_name = ""
                officer.vrchat_id = ""
                officer.deleted_at = None
                if officer.extra:
                    try:
                        del officer.extra["left_reason"]
                    except KeyError:
                        pass
                await officer.update()

                # Let all subscribers know that they may need to remove any data
                await self._notify_all(
                    MemberManagementEvent.MemberJoinedAfterMaxWait(officer, member)
                )
            else:
                officer.deleted_at = None
                if officer.extra:
                    try:
                        del officer.extra["left_reason"]
                    except KeyError:
                        pass
                log.info(
                    f"`{member.display_name}` ({member.id}) restored existing data"
                )
                await officer.update()
                # The officer can keep their data as they joined back within the grace period
                await self._notify_all(
                    MemberManagementEvent.MemberJoined(officer, member)
                )
        else:
            # A new officer needs to be created
            officer = Officer(
                id=member.id, started_monitoring=now(), vrchat_name="", vrchat_id=""
            )
            await officer.save()
            await self._notify_all(MemberManagementEvent.MemberJoined(officer, member))
            log.info(
                f"`{member.display_name}` ({member.id}) has been added to the database."
            )

        # Add the officer to the cache
        self._lpd_members[officer.id] = officer

    async def member_left_LPD(
        self,
        member_id: int,
        member: Optional[discord.Member],
        reason: str = "unknown",
    ) -> None:
        # added id because of find_missing_officers
        # no member when already left

        # Store when they were removed
        officer = await Officer.objects.get(id=member_id)
        officer.deleted_at = now()
        if not officer.extra:
            officer.extra = {}
        officer.extra["left_reason"] = reason
        await officer.update()

        # Remove them from the cache
        del self._lpd_members[officer.id]

        # Let others know
        if member:
            log.info(
                f"{member.display_name} ({member.id}) has been removed from the LPD {reason=}.\n"
                "roles= `" + ",".join([str(role.id) for role in member.roles]) + "`"
            )
        else:
            log.info(
                f"vrc:`{officer.vrchat_name}`({officer.vrchat_id})[discordId:{member_id}] has been removed from the LPD {reason=}."
            )
        await self._notify_all(
            MemberManagementEvent.MemberLeft(
                member_id,
                member,
                reason,
            )
        )

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

        if before.id in self.role_update_blocklist:
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
                await self.member_left_LPD(after.id, after, "role_removed")

        if (
            before.get_role(settings.FILMING_CREW_ROLE) == None
            and after.get_role(settings.FILMING_CREW_ROLE) != None
        ):
            await self.filming_crew.put(after)

    def add_role_update_blocklist(self, member_id: int) -> None:
        self.role_update_blocklist.add(member_id)

    def remove_role_update_blocklist(self, member_id: int) -> None:
        self.role_update_blocklist.remove(member_id)

    def clear_role_update_blocklist(self) -> None:
        self.role_update_blocklist.clear()

    @bl_listen()
    async def on_member_remove(self, member: discord.Member) -> None:
        if is_lpd_member(member) and member.guild.id == settings.SERVER_ID:
            await self.member_left_LPD(member.id, member, "left_server_online")

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
                tasks.append(
                    loop.create_task(
                        self.member_left_LPD(officer.id, member, "left_server_offline")
                    )
                )

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
        r += f"started:{of.started_monitoring.isoformat() if of.started_monitoring else 'invalid_start'}\n"
        r += f"left:{of.deleted_at.isoformat() if of.deleted_at else 'active'}\n"
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

    def get_roles_list_to_remove(self) -> list[discord.Object]:
        roles_to_remove = [
            discord.Object(settings.LPD_ROLE),
            discord.Object(settings.SLRT_TRAINED_ROLE),
            discord.Object(settings.LMT_TRAINED_ROLE),
            discord.Object(settings.WATCH_OFFICER_ROLE),
            discord.Object(settings.PROGRAMMING_TEAM_ROLE),
            discord.Object(settings.DEV_TEAM_ROLE),
            discord.Object(settings.TEAM_LEAD_ROLE),
            discord.Object(settings.EVENT_HOST_ROLE),
            discord.Object(settings.MEDIA_PRODUCTION_ROLE),
            discord.Object(settings.RECRUITER_ROLE),
            discord.Object(settings.INSTIGATOR_ROLE),
            discord.Object(settings.JANITOR_ROLE),
            discord.Object(settings.MENTOR_ROLE),
            discord.Object(settings.APPROVER_ROLE),
            discord.Object(settings.CHAT_MODERATOR_ROLE),
            discord.Object(settings.TRAINER_ROLE),
            discord.Object(settings.SLRT_TRAINER_ROLE),
            discord.Object(settings.LMT_TRAINER_ROLE),
            discord.Object(settings.PRISON_TRAINER_ROLE),
            discord.Object(settings.INSTIGATOR_TRAINER_ROLE),
            discord.Object(settings.KOREAN_ROLE),
            discord.Object(settings.CHINESE_ROLE),
            discord.Object(settings.JAPANESE_ROLE),
            discord.Object(settings.LOOKING_4_PATROL_ROLE),
            discord.Object(settings.STANDBY_ACTOR_ROLE),
            discord.Object(settings.DETECTIVE_ROLE),
            discord.Object(settings.STANDBY_LMT_ROLE),
            discord.Object(settings.STANDBY_SLRT_ROLE),
            discord.Object(settings.STANDBY_CALL_911_ROLE),
            discord.Object(settings.AGGRESSOR_ROLE),
            discord.Object(settings.PENDING_APPROVAL_ROLE),
            discord.Object(settings.EVENT_1_ROLE),
            discord.Object(settings.EVENT_2_ROLE),
        ]
        for name, rank in settings.ROLE_LADDER.items():
            if rank < settings.ROLE_LADDER.sergeant:
                roles_to_remove.append(discord.Object(rank.id))
        # last on purpuse, if atomic and problem happens
        roles_to_remove.append(discord.Object(settings.INACTIVE_ROLE))

        return roles_to_remove

    def get_role_list_blocking(self) -> set[int]:
        blocklist = set[int](
            [
                # settings.TEAM_LEAD_ROLE,
                settings.LPDPLUS_ROLE,
            ]
        )
        for name, rank in settings.ROLE_LADDER.items():
            if rank >= settings.ROLE_LADDER.sergeant:
                blocklist.add(rank.id)
        return blocklist

    async def remove_inactive_officers(
        self,
        members: list[discord.Member],
        msg: Optional[discord.Message] = None,
    ) -> bool:
        """return True if successful, False if not"""
        success = True

        roles_to_remove = self.get_roles_list_to_remove()

        blocklist = self.get_role_list_blocking()

        total = len(members)
        for i, m in enumerate(members):
            for r in m.roles:
                if r.id in blocklist:
                    log.info(
                        f"prevent inactive_rm for `{m.display_name}` because has `{r.name}`"
                    )
                    break
            else:
                self.add_role_update_blocklist(m.id)
                # Atomic=true will do a request per role to remove
                # Atomic=false will do one request per call but use cached roles
                await self.member_left_LPD(m.id, m, "inactive")
                try:
                    await m.remove_roles(
                        *roles_to_remove,
                        reason="inactive",
                        atomic=True,
                    )
                except discord.HTTPException as e:
                    log.error(f"Failed to remove roles from {m.mention} err=`{e}`")
                    if e.text:
                        log.debug(f"rm_inactive err=`{e}` {e.text}")
                    success = False
            msg = await msg.edit(content=f"Removing `{i+1:2d}/{total:2d}`...")
        self.clear_role_update_blocklist()
        return success

    async def remove_cadet(self, officers: list[models.Officer]) -> bool:
        """return True if successful, False if not"""
        lpd_role = discord.Object(settings.LPD_ROLE)
        cadet_role = discord.Object(settings.ROLE_LADDER.cadet.id)
        guild = self.bot.get_guild(settings.SERVER_ID)
        success = True
        if not guild:
            raise Exception(f"guild {settings.SERVER_ID} is not accessible")
        for o in officers:
            member = guild.get_member(o.id)
            self.add_role_update_blocklist(o.id)
            await self.member_left_LPD(o.id, member, "inactive_cadet")
            if not member:
                # log.error(f"Member[{o.id}] not found!")
                # o.delete = dt.datetime.now()
                # o.update()
                continue
            try:
                await member.remove_roles(lpd_role, cadet_role, reason="remove_cadet")
            except:
                log.exception("failed to remove cadets roles")
                success = False
        self.clear_role_update_blocklist()
        return success
