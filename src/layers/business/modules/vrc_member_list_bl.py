import asyncio
import datetime as dt
import logging
from typing import Optional
import json

import aiohttp
import discord
from discord.ext import commands, tasks

from src.layers.business.base_bl import DiscordListenerMixin, bl_listen
import settings
from settings.classes import RoleLadderElement
from src.layers.business.extra_functions import debounce, has_role_id, not_none
from src.layers.business.modules.pt_bl import PatrolTimeBL
from src.layers.storage import models

log = logging.getLogger("lpd-officer-monitor")


class VRCMemberListBL(DiscordListenerMixin):
    def __init__(self, bot: commands.Bot, pt_bl: PatrolTimeBL) -> None:
        self.bot = bot
        super().__init__()
        self.pt_bl = pt_bl
        self.last_upload_to_world = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
            hours=2
        )

    @bl_listen("on_ready")
    async def on_ready(self):
        if (
            settings.STATION_ALLOWLIST_GIST_ID is None
            or settings.STATION_ALLOWLIST_PERSONAL_ACCESS_TOKEN is None
        ):
            log.warning("`upload_to_world_task` won't work because of missing settings")
        elif not self.upload_to_world_task.is_running():
            self.upload_to_world_task.start()
        if not self.make_payments_task.is_running():
            self.make_payments_task.start()
        if not self.check_payments_task.is_running():
            self.check_payments_task.start()

    def destroy(self):
        """hard coded call !!!"""
        self.upload_to_world_task.cancel()
        self.make_payments_task.cancel()
        self.check_payments_task.cancel()

    @tasks.loop(hours=2.0)
    async def upload_to_world_task(self):
        delta = dt.datetime.now(dt.timezone.utc) - self.last_upload_to_world
        if delta < dt.timedelta(hours=6.0):
            return
        try:
            self.upload_to_world()
        except Exception as e:
            log.exception("upload_to_world_task failed and will be canceled")
            self.upload_to_world_task.stop()

    @tasks.loop(time=dt.time(hour=19, minute=0, tzinfo=dt.timezone.utc))
    async def check_payments_task(self):
        if dt.datetime.now(tz=dt.timezone.utc).weekday() <= 3:
            return  # only run after Thursdays
        last_paid: Optional[dt.datetime] = await models.Payment.objects.max("timestamp")
        last_paid = last_paid.replace(tzinfo=dt.UTC)
        now = dt.datetime.now(tz=dt.UTC)
        start_prev_week = now.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - dt.timedelta(days=now.weekday() + 7)
        end_prev_week = (start_prev_week + dt.timedelta(days=6)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        if last_paid < end_prev_week:
            log.error(
                f"@here it seems officers didn't get payed for last week!!! last_paid=<t:{int(last_paid.timestamp())}:F> "
            )
        else:
            log.debug("`chk_pay` OK")

    @tasks.loop(time=dt.time(hour=13, minute=0, tzinfo=dt.timezone.utc))
    async def make_payments_task(self):
        if dt.datetime.now(tz=dt.timezone.utc).weekday() != 3:
            return  # only run on Thursdays
        last_paid: Optional[dt.datetime] = await models.Payment.objects.max("timestamp")
        last_paid = last_paid.replace(tzinfo=dt.UTC)
        now = dt.datetime.now(tz=dt.UTC)
        start_prev_week = now.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - dt.timedelta(days=now.weekday() + 7)
        end_prev_week = (start_prev_week + dt.timedelta(days=6)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        if last_paid > end_prev_week and last_paid < now:
            log.error(
                f"`make_payments_task` canceled, payment was already done for last week it seems last_paid=<t:{int(last_paid.timestamp())}:F>"
            )
            return

        try:
            # TODO check if ressource usage is impacting service, will need to profile and add sleep until low attendance
            await self.make_payments()
            log.info("make_payments_task worked")
        except Exception as e:
            log.exception("make_payments_task failed and will be canceled")
            self.make_payments_task.stop()

    async def make_payments(self) -> None:
        now = dt.datetime.now(tz=dt.UTC)
        start_last_week = now.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - dt.timedelta(days=now.weekday() + 7)
        end_last_week = (start_last_week + dt.timedelta(days=6)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        time = await self.pt_bl.get_top_patrol_time(start_last_week, end_last_week)
        await asyncio.sleep(1)  # make sure we give ressource back to other tasks
        async with models.database.transaction():
            new_payment = await models.Payment.objects.create(timestamp=now)
            officer_payments = []
            for officer_id, duration in time.items():
                # Officers are paid 100/hour every week up to a maximum of 500
                amount = min(int((duration.total_seconds() / 3600) * 100), 500)
                officer_payment = models.OfficerPayment(
                    officer=officer_id, payment=new_payment, amount=amount
                )
                officer_payments.append(officer_payment)
            if len(officer_payments) > 0:
                await models.OfficerPayment.objects.bulk_create(officer_payments)
        log.info(f"Payed {len(officer_payments)} officers")

    @debounce(seconds=60 * 5)
    async def upload_to_world(self, reason: Optional[str] = "cron") -> None:
        """
        Uploads the member CSV to the gist where the VRChat world can download it.
        """
        self.last_upload_to_world = dt.datetime.now(dt.timezone.utc)
        string = await self.get_csv_str()
        gist_id = settings.STATION_ALLOWLIST_GIST_ID
        token = settings.STATION_ALLOWLIST_PERSONAL_ACCESS_TOKEN
        if gist_id is None or token is None or not token.startswith("ghp_"):
            log.warn(
                "Failed to upload member list to world. Station allowlist settings not "
                "fully filled out and valid."
            )
            return

        log.debug(f"Uploading member list csv to gist. {reason=}")
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
                # response_json = await response.json()
                # content_length = response.content.total_bytes

                # history = response_json.get("history", None)
                # log.debug(
                #     f"Data returned from gist edit endpoint: {content_length / 1000}KB"
                # )
                for k in response.headers:
                    if k.startswith("x-ratelimit-"):
                        print(f"{k}: `{response.headers[k]}`")

    async def get_csv_str(self) -> str:
        """
        Generates the officer CSV as a string to be output by the bot or uploaded to the
        VRChat world.
        """
        officers = (
            await models.Officer.objects.filter(models.Officer.deleted_at.isnull(True))
            .exclude(models.Officer.vrchat_name == "")
            .all()
        )
        latest_payment = await models.Payment.objects.order_by("-timestamp").first()
        payments_list = (
            await models.OfficerPayment.objects.filter(payment__id=latest_payment.id)
            .select_related("officer")
            .all()
        )
        officer_payments = {not_none(op.officer).id: op.amount for op in payments_list}

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
                "Japanese",
                "Supporter",
                "Mentor",
                "Approver",
                "Community",
                "Backroom Access",
                "Pay Date",
                "Pay Amount",
                "Event 1",
                "Event 2",
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
                has_role_id(member, settings.JAPANESE_ROLE),
                has_role_id(member, settings.SUPPORTER_ROLE),
                has_role_id(member, settings.MENTOR_ROLE),
                has_role_id(member, settings.APPROVER_ROLE),
                "LPD" if has_role_id(member, settings.LPD_ROLE) else "UKN",
                True,  # "Backroom Access",
                latest_payment.timestamp.timestamp(),
                officer_payments.get(o.id, 0),
                has_role_id(member, settings.EVENT_1_ROLE),
                has_role_id(member, settings.EVENT_2_ROLE),
            ]
            output_text += settings.NAME_SEPARATOR.join(map(str, odata)) + "\n"

        if len(settings.VRC_NAMES_STATIC) > 0:
            registered_officer_names = set[str](o.vrchat_name for o in officers)
            for staticName in settings.VRC_NAMES_STATIC:
                if staticName not in registered_officer_names:
                    odata = [
                        staticName,
                        "Guest",
                        False,  # white shirt
                        False,  # SLRT_TRAINED_ROLE
                        False,  # LMT_TRAINED_ROLE
                        False,  # WATCH_OFFICER_ROLE
                        False,  # EVENT_HOST_ROLE
                        False,  # PROGRAMMING_TEAM_ROLE
                        False,  # MEDIA_PRODUCTION_ROLE
                        False,  # CHAT_MODERATOR_ROLE
                        False,  # INSTIGATOR_ROLE
                        False,  # TRAINER_ROLE
                        False,  # SLRT_TRAINER_ROLE
                        False,  # LMT_TRAINER_ROLE
                        False,  # PRISON_TRAINER_ROLE
                        False,  # INSTIGATOR_TRAINER_ROLE
                        False,  # DEV_TEAM_ROLE
                        False,  # RECRUITER_ROLE
                        False,  # TEAM_LEAD_ROLE
                        False,  # KOREAN_ROLE
                        False,  # CHINESE_ROLE
                        False,  # JAPANESE_ROLE
                        False,  # SUPPORTER_ROLE
                        False,  # MENTOR_ROLE
                        False,  # APPROVER_ROLE
                        "LPD",
                        True,  # "Backroom Access",
                        0.0,  # payment timestamp
                        0,  # payment amount
                        False,  # EVENT_1_ROLE
                        False,  # EVENT_2_ROLE
                    ]
                    output_text += settings.NAME_SEPARATOR.join(map(str, odata)) + "\n"

        return output_text

    async def get_json_str(self) -> str:
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
                "Japenese": has_role_id(member, settings.JAPANESE_ROLE),
                "Supporter": has_role_id(member, settings.SUPPORTER_ROLE),
                "Mentor": has_role_id(member, settings.MENTOR_ROLE),
                "Approver": has_role_id(member, settings.APPROVER_ROLE),
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
                    "Supporter": False,
                    "Community": "LPD",
                    "Backroom Access": True,
                }

        # set separator to get rid of spaces
        # add lines for better human readability
        return json.dumps(jsondata, separators=(",", ":")).replace("},", "},\n")
