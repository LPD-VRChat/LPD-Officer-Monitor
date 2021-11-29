# Standard
import datetime as dt
import logging
from typing import Union

# Community
import discord
import ormar

# Custom
from .base_bl import DiscordListenerBL, bl_listen
import settings
from src.layers.storage.models import Officer

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
        officer_before = self.bot.officer_manager.is_officer(before)
        officer_after = self.bot.officer_manager.is_officer(after)

        # Nothing happened to an LPD Officer
        if officer_before is True and officer_after is True:
            return
        # Nothing happened to a regular member
        elif officer_before is False and officer_after is False:
            return

        # Member has joined the LPD
        elif officer_before is False and officer_after is True:
            # Check if officer is already in database
            # officer = await Officer.objects.get(id=after.id)
            # if officer is None:
            #     officer = await Officer.objects.get_or_create(id=before.id)
            pass

        # Member has left the LPD
        elif officer_before is True and officer_after is False:
            # await bot.officer_manager.remove_officer(
            #     before.id,
            #     reason="this person does not have the LPD role anymore",
            #     display_name=after.display_name,
            # )
            pass
