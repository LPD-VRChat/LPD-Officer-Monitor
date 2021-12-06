# Standard
import datetime as dt
import logging
from typing import Union

# Community
import discord

# Custom
import settings
from src.layers.business.extra_functions import is_lpd_member
from src.layers.storage.models import Officer
from .base_bl import DiscordListenerBL, bl_listen

log = logging.getLogger("lpd-officer-monitor")


class TimeBL(DiscordListenerBL):
    @bl_listen("on_message")
    async def process_loa(self, message: discord.Message) -> None:
        if message.channel.id == settings.LEAVE_OF_ABSENCE_CHANNEL:
            log.debug("Processing LOA")

    @bl_listen("on_member_update")
    async def member_join_leave(
        self,
        before: Union[discord.Member, discord.User],
        after: Union[discord.Member, discord.User],
    ) -> None:
        officer_before = is_lpd_member(before)
        officer_after = is_lpd_member(after)

        # Nothing happened to an LPD Officer
        if officer_before is True and officer_after is True:
            log.debug("member_join_leave - LPD officer did not do anything interesting")
            return
        # Nothing happened to a regular member
        elif officer_before is False and officer_after is False:
            log.debug(
                "member_join_leave - Regular member did not do anything interesting"
            )
            return

        # Member has joined the LPD
        elif officer_before is False and officer_after is True:
            # Get or create the officer
            officer = await Officer.objects.get_or_create(id=before.id)
            # They are given a started monitoring date no matter if they were
            # in the database or not to prevent them being removed immediately
            # for inactivity.
            officer.started_monitoring = dt.datetime.now(dt.timezone.utc)
            log.info(
                f"{after.display_name} ({after.name}#{after.discriminator}) has been added to the database."
            )

        # Member has left the LPD
        elif officer_before is True and officer_after is False:
            # We don't seem to have any way to register that they're no longer
            # in the LPD so we can't do anything to the member that left.
            log.info(
                f"{after.display_name} ({after.name}#{after.discriminator}) has been removed from the LPD."
            )
