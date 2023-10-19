# Standard
import logging
from typing import Optional
import json
import os
import subprocess

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

        for staticName in settings.VRC_NAMES_STATIC:
            if staticName not in jsondata:
                jsondata[staticName] = {
                    "Rank": settings.ROLE_LADDER.officer.name,
                    "Staff": False,
                    "SLRT Certified": False,
                    "LMT Certified": False,
                    "CO Certified": False,
                    "Event Host": False,
                    "Programmer": False,
                    "Media": False,
                    "Chatmod": False,
                    "Instigator": False,
                    "Trainer": False,
                    "SLRT Trainer": False,
                    "LMT Trainer": False,
                    "CO Trainer": False,
                    "Instigator Trainer": False,
                    "Dev": False,
                    "Recruiter": False,
                    "Lead": False,
                    "Korean": False,
                    "Chinese": False,
                    "Community": "LPD",
                    "Backroom Access": True,
                }

        # set separator to get rid of spaces
        # add lines for better human readability
        return json.dumps(jsondata, separators=(",", ":")).replace("},", "},\n")

    def _run_command(self, cmd) -> bool:
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd="repo",
                timeout=10,
            )

            if result.returncode != 0:
                log.error(
                    f"Command `{cmd}` failed({result.returncode}) : {result.stderr}"
                )
                return False
        except Exception as e:
            log.error(f"Command `{cmd}` failed : {str(e)}")
            return False
        return True

    async def export_json_list_git(self) -> bool:
        if not os.path.isdir(settings.GIT_REPO_PATH):
            log.error("repo folder does not exist")
            return False
        if not self._run_command("git reset --hard"):
            return False
        if not self._run_command("git pull"):
            # return False
            pass
        jsonData = await self.get_list_as_json()
        if len(jsonData) < 8:
            log.error(f"json looks to be invalid {len(jsonData)=}")
            return False
        with open(
            settings.GIT_REPO_PATH + os.sep + settings.GIT_REPO_FILENAME, "w"
        ) as f:
            f.write(jsonData)
        try:
            result = subprocess.run(
                "git diff",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd="repo",
                timeout=10,
            )
            if result.returncode != 0:
                log.error(f"Command diff failed({result.returncode}) : {result.stderr}")
                return False
            if len(result.stdout) == 0:
                log.info("json git export: no change")
                return True
        except Exception as e:
            log.error(f"Command diff failed : {str(e)}")
            return False
        if not self._run_command("git add allowlist.json"):
            return False
        if not self._run_command('git commit -m "Updated allowlist.json"'):
            return False
        if not self._run_command("git push"):
            return False
