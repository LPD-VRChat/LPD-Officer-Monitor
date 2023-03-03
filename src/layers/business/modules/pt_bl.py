"""
Patrol Time Business Layer

Manage the patrol time of officers and proide their patrol time to other parts
of the bot.
"""
# Standard
import asyncio
from dataclasses import dataclass
import logging
import datetime as dt
from typing import Dict, Iterable

# Community
import discord
from discord.ext import commands

# Custom
import settings
from settings.classes import RoleLadderElement
from src.layers.business.base_bl import DiscordListenerMixin, bl_listen
from src.layers.business.extra_functions import now, get_guild
from src.layers.storage import models

log = logging.getLogger("lpd-officer-monitor")


@dataclass
class PatrolLog:
    patrol: models.Patrol
    voice_logs: list[models.PatrolVoice]


class PatrolTimeBL(DiscordListenerMixin):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

        self._patrolling_officers: dict[int, PatrolLog] = {}

    def _is_on_patrol(self, member: discord.Member) -> bool:
        return member.id in self._patrolling_officers

    def _is_monitored(
        self,
        channel: discord.VoiceChannel
        | discord.StageChannel
        | discord.GroupChannel
        | None,
    ) -> bool:
        """
        Check if a channel is monitored according to the bots settings.
        """
        # Only discord voice channels can be tracked
        if not isinstance(channel, discord.VoiceChannel):
            return False

        # Store if the channel is monitored or ignored
        is_monitored = (
            channel.category is not None
            and channel.category.id in settings.ON_DUTY_CATEGORIES
        )
        is_ignored = channel.id in settings.ON_DUTY_IGNORED_CHANNELS

        # A channel is only monitored if it is monitored and not ignored
        return is_monitored and not is_ignored

    async def _get_main_channel(
        self, voice_logs: list[models.PatrolVoice]
    ) -> models.SavedVoiceChannel:
        # Go through the saved voice channels and
        # TODO: add logic to return the most probable squad
        for voice_log in voice_logs:
            channel = self.bot.get_channel(voice_log.channel.id)
            if (
                isinstance(channel, discord.VoiceChannel)
            ) and not channel.name.startswith(tuple(settings.BAD_MAIN_CHANNEL_STARTS)):
                return await self._get_saved_voice_channel(channel.id)

        # Give the first channel if no good one was found
        return await self._get_saved_voice_channel(voice_logs[0].channel_id)

    async def get_patrol_time(
        self, officer_id: int, from_dt: dt.datetime, to_dt: dt.datetime
    ) -> dt.timedelta:
        patrols = await self.get_patrols(officer_id, from_dt, to_dt)
        patrol_lengths = (p.duration() for p in patrols)
        return sum(patrol_lengths, start=dt.timedelta())

    async def get_patrols(
        self, officer_id: int, from_dt: dt.datetime, to_dt: dt.datetime
    ) -> list[models.Patrol]:
        return await models.Patrol.objects.filter(
            officer=officer_id, start__gt=from_dt, end__lt=to_dt
        ).all()

    async def get_top_patrol_time(
        self, from_dt: dt.datetime, to_dt: dt.datetime
    ) -> Dict[int, dt.timedelta]:
        patrols = await models.Patrol.objects.filter(
            start__gt=from_dt, end__lt=to_dt
        ).all()
        temp: Dict[int, dt.timedelta] = {}
        for p in patrols:
            if p.officer.id in temp:
                temp[p.officer.id] += p.duration()
            else:
                temp[p.officer.id] = p.duration()
        sortedData = {k: v for k, v in sorted(temp.items(), key=lambda item: item[1])}
        return sortedData

    async def get_patrol_voices(
        self, officer_id: int, from_dt: dt.datetime, to_dt: dt.datetime
    ) -> dict[models.Patrol, list[models.PatrolVoice]]:
        # patrols = await self.get_patrols(officer_id, from_dt, to_dt)
        # patrols_ids = {p.id: p for p in patrols}

        patrols = (
            await models.Patrol.objects.filter(
                officer=officer_id, start__gt=from_dt, end__lt=to_dt
            )
            .select_related("patrolvoices")
            .all()
        )

        return {p: p.patrolvoices for p in patrols}

    @bl_listen()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        # Make sure we're in the LPD server
        on_patrol = self._is_on_patrol(member)
        to_monitored_channel = self._is_monitored(after.channel)
        curr_time = now()

        match (on_patrol, to_monitored_channel):

            # Officer is moving between monitored channels
            case True, True:
                log.debug(
                    f"{member.display_name} ({member.id}) is switching on duty channels."
                )

                # Because is_monitored returned True the channel must be a voice channel
                assert isinstance(after.channel, discord.VoiceChannel)

                # Add a time to the latest patrol log and open a new one for the channel
                # that the officer switched into
                self._patrolling_officers[member.id].patrol.end = curr_time
                self._patrolling_officers[member.id].voice_logs[-1].end = curr_time
                async with models.database.transaction():
                    await self._patrolling_officers[member.id].patrol.update()
                    await self._patrolling_officers[member.id].voice_logs[-1].update()
                if before and (before.channel.id != after.channel.id):
                    self._patrolling_officers[member.id].voice_logs.append(
                        await models.PatrolVoice.objects.create(
                            channel=after.channel.id,
                            patrol=self._patrolling_officers[member.id].patrol,
                            start=curr_time,
                            end=curr_time,
                        )
                    )

            # Officer is going on duty
            case False, True:
                log.debug(f"{member.display_name} ({member.id}) is going on duty.")

                # Because is_monitored returned True the channel must be a voice channel
                assert isinstance(after.channel, discord.VoiceChannel)

                patrol = await models.Patrol.objects.create(
                    officer=member.id,
                    start=curr_time,
                    end=curr_time,
                    event=None,
                    main_channel=after.channel.id,
                )

                # Add the first patrol and voice log to the cache
                self._patrolling_officers[member.id] = PatrolLog(
                    patrol,
                    [
                        await models.PatrolVoice.objects.create(
                            channel=after.channel.id,
                            patrol=patrol,
                            start=curr_time,
                            end=curr_time,
                        )
                    ],
                )

            # Officer is going off duty
            case True, False:
                log.debug(f"{member.display_name} ({member.id}) is going off duty.")

                self._patrolling_officers[member.id].patrol.end = curr_time
                self._patrolling_officers[member.id].voice_logs[-1].end = curr_time
                async with models.database.transaction():
                    await self._patrolling_officers[member.id].patrol.update()
                    await self._patrolling_officers[member.id].voice_logs[-1].update()

                # Remove the patrol from the cache as it is now in the database
                del self._patrolling_officers[member.id]

            # Nothing special happened
            case _, _:
                pass

    @bl_listen()
    async def on_ready(self):
        curr_time = now()
        channel: discord.VoiceChannel
        for channel in self.bot.guild.channels:
            model, _ = await models.SavedVoiceChannel.objects.get_or_create(
                id=channel.id,
                _defaults={
                    "guild_id": settings.SERVER_ID,
                    "name": channel.name,
                },
            )
            if self._is_monitored(channel):
                for member in channel.members:
                    patrol = await models.Patrol.objects.create(
                        officer=member.id,
                        start=curr_time,
                        end=curr_time,
                        event=None,
                        main_channel=channel.id,
                    )
                    self._patrolling_officers[member.id] = PatrolLog(
                        patrol,
                        [
                            await models.PatrolVoice.objects.create(
                                channel=channel.id,
                                patrol=patrol,
                                start=curr_time,
                                end=curr_time,
                            )
                        ],
                    )

    async def on_unload(self):
        curr_time = now()
        for officer_id in self._patrolling_officers:
            self._patrolling_officers[officer_id].patrol.end = curr_time
            self._patrolling_officers[officer_id].voice_logs[-1].end = curr_time
            async with models.database.transaction():
                await self._patrolling_officers[officer_id].patrol.update()
                await self._patrolling_officers[officer_id].voice_logs[-1].update()
        self._patrolling_officers.clear()

    async def get_potential_officer_promotion(
        self, from_date: dt.datetime, minimum_hours: int
    ) -> list[models.Officer]:
        guild = self.bot.get_guild(settings.SERVER_ID)
        if not guild:
            logging.error(f"guild {settings.SERVER_ID} is not accessible")
            return []

        role = guild.get_role(settings.ROLE_LADDER.recruit.id)
        if role is None:
            logging.error(
                f"recruit role {settings.ROLE_LADDER.recruit.id} is not accessible"
            )
            return []

        officer_ids = [m.id for m in role.members]
        # from_dt = now() - dt.timedelta(days=15)
        to_dt = now()

        patrols = await models.Patrol.objects.filter(
            officer__in=officer_ids, start__gt=from_date, end__lt=to_dt
        ).all()

        # patrolling_times:dict[int,dt.timedelta] = {key: dt.timedelta() for key in officer_ids}
        patrolling_times = {key: dt.timedelta() for key in officer_ids}
        for p in patrols:
            patrolling_times[p.officer.id] += p.duration()

        requirement = dt.timedelta(hours=minimum_hours)
        officer_to_promote_ids: list[int] = []
        for officer_id in patrolling_times:
            if patrolling_times[officer_id] > requirement:
                officer_to_promote_ids.append(officer_id)

        officers = await models.Officer.objects.filter(
            id__in=officer_to_promote_ids
        ).all()
        return officers

    async def get_officer_bellow_patrol_time(
        self, from_date: dt.datetime, minimum_hours: int
    ) -> list[models.Officer]:
        guild = self.bot.get_guild(settings.SERVER_ID)
        if not guild:
            logging.error(f"guild {settings.SERVER_ID} is not accessible")
            return []

        def add_members_from_role(role: RoleLadderElement, list: list[discord.Member]):
            discord_role = guild.get_role(role.id)
            if discord_role is None:
                logging.error(f"{role.name} role {role.id} is not accessible")
                return
            list.extend([m.id for m in discord_role.members])

        officer_ids: list[int] = []
        add_members_from_role(settings.ROLE_LADDER.officer, officer_ids)
        add_members_from_role(settings.ROLE_LADDER.senior_officer, officer_ids)
        add_members_from_role(settings.ROLE_LADDER.corporal, officer_ids)
        add_members_from_role(settings.ROLE_LADDER.sergeant, officer_ids)
        to_dt = now()

        patrols = await models.Patrol.objects.filter(
            officer__in=officer_ids, start__gt=from_date, end__lt=to_dt
        ).all()

        # patrolling_times:dict[int,dt.timedelta] = {key: dt.timedelta() for key in officer_ids}
        patrolling_times = {key: dt.timedelta() for key in officer_ids}
        for p in patrols:
            patrolling_times[p.officer.id] += p.duration()
            await asyncio.sleep(0)
        requirement = dt.timedelta(hours=minimum_hours)

        officerid_to_yeet_ids: list[int] = []
        for oid in officer_ids:
            if oid not in patrolling_times:
                officerid_to_yeet_ids.append(oid)
            else:
                if patrolling_times[oid] < requirement:
                    officerid_to_yeet_ids.append(oid)

        officers = await models.Officer.objects.filter(
            id__in=officerid_to_yeet_ids
        ).all()
        return officers

    def get_patrolling_officers(
        self,
    ) -> dict[int, list[int]]:
        """key is channel_id, array of officer_id"""
        result: dict[int, list[int]] = {}
        for officer_id, data in self._patrolling_officers.items():
            if data.voice_logs[-1].channel_id in result:
                result[data.voice_logs[-1].channel_id].append(officer_id)
            else:
                result[data.voice_logs[-1].channel_id] = [officer_id]
        return result
