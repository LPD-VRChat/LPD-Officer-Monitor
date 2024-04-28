import logging
from typing import Optional

import aiohttp
import discord
from discord.ext import commands

import settings
from settings.classes import RoleLadderElement
from src.layers.business.extra_functions import debounce, has_role_id
from src.layers.storage import models

log = logging.getLogger("lpd-officer-monitor")


class VRCMemberListBL:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @debounce(seconds=60)
    async def upload_to_world(self) -> None:
        string = await self.get_csv_str()
        gist_id = settings.STATION_ALLOWLIST_GIST_ID
        token = settings.STATION_ALLOWLIST_PERSONAL_ACCESS_TOKEN
        if gist_id is None or token is None or not token.startswith("ghp_"):
            log.warn(
                "Failed to upload member list to world. Station allowlist settings not "
                "fully filled out and valid."
            )
            return

        log.info("Uploading member list csv to gist.")
        async with aiohttp.ClientSession() as session:
            url = f"https://api.github.com/gists/{gist_id}"
            headers = {
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            json = {"files": {"station_allowlist.csv": {"content": string}}}
            async with session.patch(url, headers=headers, json=json) as response:
                if response.status != 200:
                    error_msg = response.text()
                    log.error(
                        f"Updating github gist API returned {response.status}:\n"
                        f"{error_msg}"
                    )
                response_json = await response.json()
                content_length = response.content.total_bytes

                __import__("pprint").pprint(response_json)
                history = response_json.get("history", None)
                log.info(
                    f"Data returned from gist edit endpoint: {content_length / 1000}KB"
                )
                log.info(
                    f"Number of items in history: "
                    f"{0 if history is None else len(history)}"
                )

    async def get_csv_str(self) -> str:
        officers = (
            await models.Officer.objects.filter(models.Officer.deleted_at.isnull(True))
            .exclude(models.Officer.vrchat_name == "")
            .all()
        )
        print("Officers:", officers, "#" * 30)

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

        output_text = ""
        output_text += settings.NAME_SEPARATOR.join(
            [
                "Name",
                "Rank",
                "Staff",
                "SLRT Certified",
                "LMT Certified",
                "CO Certified",
                "Event Host",
                "Programmer",
                "Media",
                "Chatmod",
                "Instigator",
                "Trainer",
                "SLRT Trainer",
                "LMT Trainer",
                "CO Trainer",
                "Instigator Trainer",
                "Dev",
                "Recruiter",
                "Lead",
                "Korean",
                "Chinese",
                "Community",
                "Backroom Access",
            ]
        )
        output_text += "\n"

        for o in officers:
            member = o.member(self.bot)
            if not member:
                log.error(f"officer {o.id} isn't on discord")
                continue
            rank = get_lpd_member_rank_local(member)
            if not rank:
                log.error(f"officer {o.id} does not have a rank")
                continue

            odata = [
                o.vrchat_name,
                rank.name,
                rank.is_white_shirt,
                has_role_id(member, settings.SLRT_TRAINED_ROLE),
                has_role_id(member, settings.LMT_TRAINED_ROLE),
                has_role_id(member, settings.WATCH_OFFICER_ROLE),
                has_role_id(member, settings.EVENT_HOST_ROLE),
                has_role_id(member, settings.PROGRAMMING_TEAM_ROLE),
                has_role_id(member, settings.MEDIA_PRODUCTION_ROLE),
                has_role_id(member, settings.CHAT_MODERATOR_ROLE),
                has_role_id(member, settings.INSTIGATOR_ROLE),
                has_role_id(member, settings.TRAINER_ROLE),
                has_role_id(member, settings.SLRT_TRAINER_ROLE),
                has_role_id(member, settings.LMT_TRAINER_ROLE),
                has_role_id(member, settings.PRISON_TRAINER_ROLE),
                has_role_id(member, settings.INSTIGATOR_TRAINER_ROLE),
                has_role_id(member, settings.DEV_TEAM_ROLE),
                has_role_id(member, settings.RECRUITER_ROLE),
                has_role_id(member, settings.TEAM_LEAD_ROLE),
                has_role_id(member, settings.KOREAN_ROLE),
                has_role_id(member, settings.CHINESE_ROLE),
                "LPD" if has_role_id(member, settings.LPD_ROLE) else "UKN",
                True,  # "Backroom Access",
            ]
            output_text += settings.NAME_SEPARATOR.join(map(str, odata)) + "\n"
        return output_text
