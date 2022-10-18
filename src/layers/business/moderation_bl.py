# Standard
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Set
import logging
import datetime as dt
import re
from urllib.parse import urlparse

# Community
import discord
from discord.ext import commands

# Custom
import settings
from src.layers.business.base_bl import DiscordListenerMixin, bl_listen

if TYPE_CHECKING:
    from .bl_wrapper import BusinessLayerWrapper


log = logging.getLogger("lpd-officer-monitor")


@dataclass
class GiftCacheObject:
    discord_id: int
    last_send_time: dt.datetime = field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc)
    )
    count: int = 0
    messages: List[discord.Message] = field(default_factory=list)
    links: Set[str] = field(default_factory=set)


class ModerationBL(DiscordListenerMixin):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot

    async def _detention_user(
        self,
        discord_id: int,
        reason: str,
        full_reason: Optional[str],
    ):
        full_reason = full_reason or reason
        member_to_detain: discord.Member = self.bot.guild.get_member(discord_id)

        # Add the needed roles
        detention_role = self.bot.guild.get_role(settings.DETENTION_WAITING_AREA_ROLE)
        permission_removal_role = self.bot.guild.get_role(settings.DETENTION_ROLE)
        await member_to_detain.add_roles(detention_role, permission_removal_role)

        # Let the user know
        await member_to_detain.send(
            f"You have been detained in the Discord Server {self.bot.guild} because you {reason}. Please wait for a staff member to take a look at your case."
        )

        # Let staff know a user is waiting for them
        mod_log = self.bot.guild.get_channel(settings.MOD_LOG_CHANNEL)
        mod_role: discord.Role = self.bot.guild.get_role(settings.MODERATOR_ROLE)
        # TODO: Add "{mod_role.mention} " back to the start of the string
        await mod_log.send(
            f"{member_to_detain.mention} has been placed in detention because they {full_reason}"
        )

    @bl_listen("on_ready")
    async def setup_cache(self):
        # TODO: Change this so that it runs in class __init__, not on_ready
        self._sent_gift_links: Dict[int, GiftCacheObject] = {}
        self._URL_REGEX = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )

    @bl_listen("on_message")
    async def remove_scam_links(self, message: discord.Message):
        urls = re.findall(self._URL_REGEX, message.content)
        for url in urls:
            p_url = urlparse(url)
            if p_url.netloc.endswith(".gift") and not p_url.netloc.endswith(
                "/discord.gift"
            ):
                user_id = message.author.id
                cache_obj = self._sent_gift_links.get(user_id, GiftCacheObject(user_id))

                # Skip if this channel has already been sent to and counted
                used_channels = {m.channel for m in cache_obj.messages}
                if message.channel in used_channels:
                    break

                # Count the message as it contains a questionable URL
                max_wait = cache_obj.last_send_time + dt.timedelta(
                    seconds=settings.GIFT_LINK_EXPIRATION_SECONDS
                )
                if max_wait < dt.datetime.now(dt.timezone.utc):
                    cache_obj.count = 1
                    cache_obj.messages = []
                    cache_obj.links = set()
                else:
                    cache_obj.count += 1
                cache_obj.last_send_time = dt.datetime.now(dt.timezone.utc)
                cache_obj.messages.append(message)
                cache_obj.links.add(url)
                self._sent_gift_links[user_id] = cache_obj

                # User has sent too many and will be put in detention and their messages deleted
                if cache_obj.count >= settings.GIFT_LINK_MAX_CHANNEL_COUNT:

                    # Reset the users cache
                    del self._sent_gift_links[user_id]

                    # Place the user in detention
                    full_reason = "were spamming questionable links (possibly discord nitro scam links) in multiple channels. Links:\n"
                    full_reason += "\n".join(f"`{l}`" for l in cache_obj.links)
                    await self._detention_user(
                        user_id,
                        reason="were spamming questionable links in multiple channels",
                        full_reason=full_reason,
                    )

                    # Remove their past messages
                    for old_message in cache_obj.messages:
                        await old_message.delete()

                break