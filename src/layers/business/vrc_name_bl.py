# Standard
import logging
from typing import Optional
import json

# external
import discord
from discord.ext import commands

# Custom
import settings
from .base_bl import DiscordListenerMixin, bl_listen
from src.layers.storage import models
from settings.classes import RoleLadderElement
from src.layers.business.extra_functions import has_role_id

log = logging.getLogger("lpd-officer-monitor")


class VRChatBL(DiscordListenerMixin):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        super().__init__()

    async def get_list_as_json(self) -> str:
        officers = (
            await models.Officer.objects.filter(models.Officer.deleted_at.isnull(True))
            .exclude(models.Officer.vrchat_name == "")
            .order_by("id")
            .all()
        )

        # because we get all ranks and inverted the order to replicate
        # the old behavior we need to do a local version of the function
        all_ranks = list(reversed(settings.ROLE_LADDER.__dict__.values()))

        def get_lpd_member_rank_local(
            member: discord.Member,
        ) -> Optional[RoleLadderElement]:
            for rank in all_ranks:
                if has_role_id(member, rank.id):
                    return rank
            return None

        jsondata = dict()

        for o in officers:
            member = o.member(self.bot)
            if not member:
                log.error(f"officer {o.id} isn't on discord")
                continue
            rank = get_lpd_member_rank_local(member)
            if not rank:
                log.error(f"officer {o.id} does not have a rank")
                continue

            jsondata[o.vrchat_name] = {
                "Rank": rank.name,
                "Staff": rank.is_white_shirt,
                "SLRT Certified": has_role_id(member, settings.SLRT_TRAINED_ROLE),
                "LMT Certified": has_role_id(member, settings.LMT_TRAINED_ROLE),
                "CO Certified": has_role_id(member, settings.WATCH_OFFICER_ROLE),
                "Event Host": has_role_id(member, settings.EVENT_HOST_ROLE),
                "Programmer": has_role_id(member, settings.PROGRAMMING_TEAM_ROLE),
                "Media": has_role_id(member, settings.MEDIA_PRODUCTION_ROLE),
                "Chatmod": has_role_id(member, settings.CHAT_MODERATOR_ROLE),
                "Instigator": has_role_id(member, settings.INSTIGATOR_ROLE),
                "Trainer": has_role_id(member, settings.TRAINER_ROLE),
                "SLRT Trainer": has_role_id(member, settings.SLRT_TRAINER_ROLE),
                "LMT Trainer": has_role_id(member, settings.LMT_TRAINER_ROLE),
                "CO Trainer": has_role_id(member, settings.PRISON_TRAINER_ROLE),
                "Instigator Trainer": has_role_id(
                    member, settings.INSTIGATOR_TRAINER_ROLE
                ),
                "Dev": has_role_id(member, settings.DEV_TEAM_ROLE),
                "Recruiter": has_role_id(member, settings.RECRUITER_ROLE),
                "Lead": has_role_id(member, settings.TEAM_LEAD_ROLE),
                "Korean": has_role_id(member, settings.KOREAN_ROLE),
                "Chinese": has_role_id(member, settings.CHINESE_ROLE),
                "Community": "LPD" if has_role_id(member, settings.LPD_ROLE) else "UKN",
                "Backroom Access": True,
            }

        # set separator to get rid of spaces
        # add lines for better human readability
        return json.dumps(jsondata, separators=(",", ":")).replace("},", "},\n")
