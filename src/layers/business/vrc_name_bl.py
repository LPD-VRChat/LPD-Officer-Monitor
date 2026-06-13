# Standard
import enum
import logging
from typing import Optional
import json
import os
import subprocess
import time
from http.cookiejar import Cookie
import asyncio
import re


# external
import discord
import ormar
from discord.ext import commands
import vrchatapi
from vrchatapi.api import authentication_api
from vrchatapi.exceptions import UnauthorizedException
from vrchatapi.models.two_factor_auth_code import TwoFactorAuthCode
from vrchatapi.models.two_factor_email_code import TwoFactorEmailCode


# Custom
import settings
from .base_bl import (
    DiscordListenerMixin,
    MemberManagementEvent,
    EventSenderMixin,
    bl_listen,
    business_event,
)
from src.layers.storage import models
from settings.classes import RoleLadderElement
from src.layers.business.extra_functions import has_role_id

log = logging.getLogger("lpd-officer-monitor")

uuidhex = re.compile(
    "^^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I
)
VRC_UUID_USER_PREFIX = "usr_"


class RateLimiter:
    def __init__(self, default_rate: int, default_per: float):
        self.default_rate = default_rate
        self.default_per = default_per

        self.effective_rate = default_rate
        self.effective_per = default_per

        self.tokens = default_rate
        self.last_update = time.time()
        self.lock = asyncio.Lock()

        self.last_request_time = 0.0
        self.burst_interval = 0.5

    async def acquire(self):
        async with self.lock:
            now = time.time()

            if self.last_request_time > 0:
                time_since_last = now - self.last_request_time
                if time_since_last < self.burst_interval:
                    wait_time = self.burst_interval - time_since_last
                    await asyncio.sleep(wait_time)
                    now = time.time()

            time_passed = now - self.last_update
            self.tokens = min(
                self.effective_rate,
                self.tokens + time_passed * (self.effective_rate / self.effective_per),
            )
            self.last_update = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) * (
                    self.effective_per / self.effective_rate
                )
                await asyncio.sleep(wait_time)
                self.tokens = 1
                self.last_update = time.time()

            self.tokens -= 1
            self.last_request_time = time.time()

    def update_from_headers(self, headers: dict):
        """
        Update rate limits from server response headers.
        Parses X-RateLimit-* headers and uses the minimum of default and server values.

        Args:
            headers: Dictionary of HTTP response headers (case-insensitive keys)
        """
        if not headers:
            return

        normalized_headers = {k.lower(): v for k, v in headers.items()}

        rate_limit_str = normalized_headers.get("x-ratelimit-limit")
        rate_limit_reset_str = normalized_headers.get("x-ratelimit-reset")

        if rate_limit_str and rate_limit_reset_str:
            try:
                server_rate = int(rate_limit_str)
                reset_value = float(rate_limit_reset_str)

                current_time = time.time()
                if reset_value > current_time:
                    server_per = reset_value - current_time
                else:
                    server_per = reset_value

                if server_per > 0 and server_per < 86400:
                    default_rps = self.default_rate / self.default_per
                    server_rps = server_rate / server_per

                    if server_rps < default_rps:
                        self.effective_rate = server_rate
                        self.effective_per = server_per
                    else:
                        self.effective_rate = self.default_rate
                        self.effective_per = self.default_per

                    self.tokens = min(self.tokens, self.effective_rate)
            except (ValueError, TypeError) as e:
                log.debug(f"Failed to parse rate limit headers: {e}")


def make_cookie(name, value):
    return Cookie(
        0,
        name,
        value,
        None,
        False,
        "api.vrchat.cloud",
        True,
        False,
        "/",
        False,
        False,
        173106866300,
        False,
        None,
        None,
        {},
    )


class VrcNotWorking(BaseException):
    pass


class VrcUserRegistrationStatus(enum.Enum):
    UNREGISTERED = 0
    OLD_NAME_ONLY = 1  # unverified
    UNVERIFIED_UUID = 2
    FOUND_NO_INVITE = 3
    GROUPINVITE_SENT = 4
    GROUPREGISTERED = 5


class LinkSearchResult(enum.Enum):
    OK = 0
    VRCAPI_DOWN = 1
    INVITE_BROKEN = 2
    USER_SEARCH_DISABLED = 3
    ERROR = -1
    INVALID_UUID = -2


class LinkInviteResult(enum.Enum):
    OK = 0
    ALREADY_INVITED = 1
    ERROR = -1


class VRChatBL(DiscordListenerMixin, EventSenderMixin):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        super().__init__()
        self.logged_in = False
        self.working = False
        self.enabled = True
        configuration = vrchatapi.Configuration(
            username=settings.VRC_USERNAME,
            password=settings.VRC_PASSWORD,
        )
        self.api_client = vrchatapi.ApiClient(configuration)
        # Set our User-Agent as per VRChat Usage Policy
        self.api_client.user_agent = "LPDBOT/3.0.0 discord.gg/lpd@thomatoes50"
        self.api_client.rest_client.cookie_jar.set_cookie(
            make_cookie("auth", settings.iniconfig.get("VRC", "auth", fallback=""))
        )
        self.api_client.rest_client.cookie_jar.set_cookie(
            make_cookie(
                "twoFactorAuth",
                settings.iniconfig.get("VRC", "twoFactorAuth", fallback=""),
            )
        )
        self.vrc_auth_api = authentication_api.AuthenticationApi(self.api_client)
        self.rate_limiter = RateLimiter(default_rate=60, default_per=60.0)
        if len(settings.VRC_GROUP_ID) == 0:
            log.warning(f"vrc group id not set, will be unable to invite")

    @bl_listen("on_connect")
    async def start(self):
        if settings.VRC_ENABLED and not self.logged_in:
            await self.login()

    async def set_enabled(self, new_state: bool) -> None:
        if new_state and not self.enabled and not self.logged_in:
            await self.login()
        self.enabled = new_state

    async def _log_api_header(self, header: dict):
        for k, v in header:
            if k.startswith("x-vrc-api-"):
                log.debug(f"{k}: {v}")

    async def log_api_version(self, exception=None):
        if exception:
            if hasattr(exception, "headers") and exception.headers:
                self._log_api_header(exception.headers)
            elif hasattr(exception, "response") and exception.response:
                self._log_api_header(exception.response.headers)
        else:
            if hasattr(self.api_client.rest_client, "last_response"):
                response = self.api_client.rest_client.last_response
                if response and hasattr(response, "headers"):
                    self._log_api_header(response.headers)
            elif (
                hasattr(self.api_client.rest_client, "response")
                and self.api_client.rest_client.response
            ):
                response = self.api_client.rest_client.response
                if hasattr(response, "headers"):
                    self._log_api_header(response.headers)

    async def login(self) -> None:
        if not settings.VRC_ENABLED:
            log.warning("login not allowed, vrc is disabled in settings")
            return
        await self.rate_limiter.acquire()
        if self.working:
            log.warning("already logged in")
            return
        try:
            thread = self.vrc_auth_api.get_current_user(async_req=True)
            current_user = thread.get()
            self._update_rate_limits_from_response()
        except UnauthorizedException as e:
            if e.status == 200:
                if "2 Factor Authentication" in e.reason:
                    import pyotp

                    totp = pyotp.TOTP(settings.VRC_2FA_SECRET)
                    t = self.vrc_auth_api.verify2_fa(
                        two_factor_auth_code=TwoFactorAuthCode(totp.now()),
                        async_req=True,
                    )
                    r = t.get()
                    print("verify2_fa", r)
                    thread = self.vrc_auth_api.get_current_user(async_req=True)
                    current_user = thread.get()
                else:
                    log.info(f"VRC Login UnauthorizedException: {e.reason}")
                    self.working = False
                    await self.log_api_version()
                    return

            else:
                log.exception("UnauthorizedException API")
                self.working = False
                self._update_rate_limits_from_exception(e)
                await self.log_api_version()
                return
        except vrchatapi.ApiException as e:
            log.exception("Exception when calling API")
            self._update_rate_limits_from_exception(e)
            await self.log_api_version()
            self.working = False
            return

        await self.log_api_version()
        cookie_jar = self.api_client.rest_client.cookie_jar._cookies[
            "api.vrchat.cloud"
        ]["/"]
        settings.iniconfig.set("VRC", "auth", cookie_jar["auth"].value)
        settings.iniconfig.set(
            "VRC", "twoFactorAuth", cookie_jar["twoFactorAuth"].value
        )
        settings.save_ini()
        self.working = True
        self.logged_in = True
        log.debug("VRC Logged in as:" + current_user.display_name)

    async def status(self) -> dict:
        r = {
            "working": self.working,
            "enabled": self.enabled and settings.VRC_ENABLED,
            "logged_in": self.logged_in,
            "feature_vrc_enabled": settings.VRC_ENABLED,
            "feature_user_search": settings.VRC_FEAT_USER_SEARCH,
            "feature_display_user_image": settings.VRC_FEAT_DISPLAY_USER_IMAGE,
        }
        if self.enabled and self.logged_in:
            try:
                await self.rate_limiter.acquire()
                t = self.vrc_auth_api.get_current_user(async_req=True)
                current_user = t.get()
                r["display_name"] = current_user.display_name
                self._update_rate_limits_from_response()
            except UnauthorizedException as e:
                r["error"] = (
                    f"Login failed UnauthorizedException `{e.body}` `{e.reason}`"
                )
                self._update_rate_limits_from_exception(e)
            except vrchatapi.ApiException as e:
                r["error"] = f"Login failed ApiException `{e.body}`"
                self._update_rate_limits_from_exception(e)

            try:
                self.allowed_to_run()
                gi = await self.get_group_invites()
                r["pending_invites"] = len(gi)
                for i in gi:
                    print(
                        f"{i['accepted_by_display_name']} added {i['user']['display_name']}{i['user']['id']}"
                    )
            except VrcNotWorking:
                pass

        return r

    def _update_rate_limits_from_response(self):
        try:
            if hasattr(self.api_client.rest_client, "last_response"):
                response = self.api_client.rest_client.last_response
                if response and hasattr(response, "headers"):
                    self.rate_limiter.update_from_headers(response.headers)
            elif (
                hasattr(self.api_client.rest_client, "response")
                and self.api_client.rest_client.response
            ):
                response = self.api_client.rest_client.response
                if hasattr(response, "headers"):
                    self.rate_limiter.update_from_headers(response.headers)
        except Exception as e:
            log.debug(f"Could not extract rate limit headers from response: {e}")

    def _update_rate_limits_from_exception(self, exception):
        try:
            if hasattr(exception, "headers") and exception.headers:
                self.rate_limiter.update_from_headers(exception.headers)
            elif hasattr(exception, "response") and exception.response:
                if hasattr(exception.response, "headers"):
                    self.rate_limiter.update_from_headers(exception.response.headers)
        except Exception as e:
            log.debug(f"Could not extract rate limit headers from exception: {e}")

    def allowed_to_run(self):
        if not (self.working and self.enabled and self.logged_in):
            raise VrcNotWorking()

    async def lookup_username(self, username: str) -> list[dict]:
        if not settings.VRC_FEAT_USER_SEARCH:
            log.warning("lookup_usr called when disabled")
            return dict()
        self.allowed_to_run()
        await self.rate_limiter.acquire()

        api_instance = vrchatapi.UsersApi(self.api_client)
        try:
            t = api_instance.search_users(
                search=username,
                n=5,
                async_req=True,
            )
            api_response = t.get()
            return api_response
        except vrchatapi.ApiException as e:
            log.exception(f"Exception when calling UsersApi->get_user: %s\n" % e)
            return dict()

    async def lookup_userid(self, user_id: str) -> Optional[vrchatapi.User]:
        self.allowed_to_run()
        await self.rate_limiter.acquire()
        api_instance = vrchatapi.UsersApi(self.api_client)

        try:
            t = api_instance.get_user(user_id, async_req=True)
            api_response = t.get()
            # print(api_response)
            return api_response
        except vrchatapi.ApiException as e:
            log.exception(f"Exception when calling UsersApi->get_user: %s\n" % e)
            return None

    async def _link_old(self, officer: models.Officer, name: str = "", id: str = ""):
        officer.vrchat_name = name
        officer.vrchat_id = id
        if officer.extra is None:
            officer.extra = {}
        officer.extra["vrcRegStatus"] = (
            VrcUserRegistrationStatus.UNVERIFIED_UUID.value
            if len(name) == 0
            else VrcUserRegistrationStatus.OLD_NAME_ONLY.value
        )
        await officer.update()

    async def link_search(
        self, discord_id: int, txt: str
    ) -> tuple[LinkSearchResult, Optional[list]]:
        try:
            officer = await models.Officer.objects.get(id=discord_id)
        except ormar.NoMatch:
            log.error(f"officer {discord_id} is not registered")
            return LinkSearchResult.ERROR, None

        id = ""
        if txt.startswith("https://vrchat.com/home/user/usr_"):
            id = VRC_UUID_USER_PREFIX + uuidhex.match(txt[33:]).string
            if not id:
                return LinkSearchResult.INVALID_UUID, None
        elif txt.startswith(VRC_UUID_USER_PREFIX):
            id = VRC_UUID_USER_PREFIX + uuidhex.match(txt[4:]).string
            if not id:
                return LinkSearchResult.INVALID_UUID, None
        elif uuidhex.match(txt):
            id = VRC_UUID_USER_PREFIX + txt

        if len(id):
            await self._link_old(officer, id=id)
            try:
                user = [await self.lookup_userid(id)]
            except VrcNotWorking:
                return LinkSearchResult.VRCAPI_DOWN, None
        else:
            if not settings.VRC_FEAT_USER_SEARCH:
                return LinkSearchResult.USER_SEARCH_DISABLED, None
            await self._link_old(officer, name=txt)
            try:
                user = await self.lookup_username(txt)
            except VrcNotWorking:
                return LinkSearchResult.VRCAPI_DOWN, []

        return LinkSearchResult.OK, user

    async def link_vrc(self, discord_id: int, vrc_uuid: str, vrc_display_name: str):
        officer = await models.Officer.objects.get(id=discord_id)
        officer.vrchat_name = vrc_display_name
        officer.vrchat_id = vrc_uuid
        if officer.extra is None:
            officer.extra = {}
        officer.extra["vrcRegStatus"] = VrcUserRegistrationStatus.FOUND_NO_INVITE.value
        await officer.update()

    async def link_group_invite(
        self, discord_id: int, vrc_uuid: str, vrc_display_name: str
    ) -> LinkInviteResult:

        if len(settings.VRC_GROUP_ID) == 0:
            log.warning(f"vrc group id not set, cannot invite")
            return LinkInviteResult.ERROR

        # no need to accept existing request, if user already requested and we send invite, vrc accept and user become member directly

        gir = vrchatapi.CreateGroupInviteRequest(user_id=vrc_uuid)
        group_api = vrchatapi.GroupsApi(self.api_client)
        try:
            await self.rate_limiter.acquire()
            t = group_api.create_group_invite(
                group_id=settings.VRC_GROUP_ID,
                create_group_invite_request=gir,
                async_req=True,
            )
            r = t.get()
            log.debug(f"invite sent {vrc_uuid} {r=}")
        except vrchatapi.ApiException as e:
            if e.body and len(e.body):
                body = json.loads(e.body)
                if hasattr(body, "error") and hasattr(body["error"], "message"):
                    if body["error"]["message"].endswith("is already invited․"):
                        return LinkInviteResult.ALREADY_INVITED
            log.exception("fail to send invite")
            return LinkInviteResult.ERROR
        except:
            log.exception("fail to send invite")
            return LinkInviteResult.ERROR

        officer = await models.Officer.objects.get(id=discord_id)
        officer.vrchat_name = vrc_display_name
        officer.vrchat_id = vrc_uuid
        if officer.extra is None:
            officer.extra = {}
        officer.extra["vrcRegStatus"] = VrcUserRegistrationStatus.GROUPINVITE_SENT.value
        await officer.update()

        return LinkInviteResult.OK

    async def get_group_invites(self):
        group_api = vrchatapi.GroupsApi(self.api_client)
        pending = []
        try:
            current_offset = 0
            while True:
                await self.rate_limiter.acquire()
                t = group_api.get_group_invites(
                    group_id=settings.VRC_GROUP_ID,
                    n=60,
                    offset=current_offset,
                    async_req=True,
                )
                r = t.get()
                pending.extend(r)
                if len(r) < 60:
                    break
        except:
            log.exception("fail to retrieve invites")
        return pending

    async def sync(self, list_unkown: bool = False) -> dict:
        group_api = vrchatapi.GroupsApi(self.api_client)

        vrcmembers = []
        try:
            current_offset = 0
            while True:
                await self.rate_limiter.acquire()
                t = group_api.get_group_members(
                    group_id=settings.VRC_GROUP_ID,
                    n=60,
                    offset=current_offset,
                    async_req=True,
                )
                r = t.get()
                vrcmembers.extend(r)
                if len(r) < 60:
                    break
        except:
            log.exception("fail to retrieve invites")

        vrcid_to_member = {m.user.id: i for i, m in enumerate(vrcmembers)}
        vrcname_to_member = {m.user.display_name: i for i, m in enumerate(vrcmembers)}

        officers = await models.Officer.objects.all(deleted_at=None)
        officers_synced = dict()

        report = {
            "migrated": 0,
            "synced": 0,
            "newsync": 0,
            "groupUnk": 0,
            "notGrouped": 0,
        }

        for o in officers:
            if (
                o.vrchat_name
                and len(o.vrchat_name)
                and (not o.vrchat_id or len(o.vrchat_id) == 0)
            ):
                if o.vrchat_name in vrcname_to_member:
                    vrcinfo = vrcmembers[vrcname_to_member[o.vrchat_name]].user
                    o.vrchat_id = vrcinfo.id
                    if o.extra is None:
                        o.extra = {}
                    o.extra["vrcRegStatus"] = (
                        VrcUserRegistrationStatus.GROUPREGISTERED.value
                    )
                    await o.update()
                    log.debug(
                        f"migrate {o.vrchat_name} to `{vrcinfo.display_name}``{vrcinfo.id}`"
                    )
                    report["migrated"] += 1
                    officers_synced[vrcinfo.id] = o.id
                else:
                    report["notGrouped"] += 1
            elif o.vrchat_id and len(o.vrchat_id):
                vrcidx = vrcid_to_member.get(o.vrchat_id)
                if vrcidx == None:
                    report["notGrouped"] += 1
                else:
                    vrcinfo = vrcmembers[vrcidx].user
                    if o.vrchat_name != vrcinfo.display_name:
                        log.debug(
                            f"vrc renamed did{o.id} `{o.vrchat_name}`->`{vrcinfo.display_name}`"
                        )
                        o.vrchat_name = vrcinfo.display_name
                        await o.update()
                    report["synced"] += 1
                    officers_synced[vrcinfo.id] = o.id
                    if o.extra is None:
                        o.extra = {
                            "vrcRegStatus": VrcUserRegistrationStatus.GROUPREGISTERED.value
                        }
                        await o.update()
                    elif (
                        o.extra.get(
                            "vrcRegStatus", VrcUserRegistrationStatus.UNREGISTERED
                        )
                        != VrcUserRegistrationStatus.GROUPREGISTERED.value
                    ):
                        o.extra["vrcRegStatus"] = (
                            VrcUserRegistrationStatus.GROUPREGISTERED.value
                        )
                        await o.update()
            else:
                report["notGrouped"] += 1

        if list_unkown:
            report["unkown"] = []

        for vrcm in vrcmembers:
            if vrcm.user.id not in officers_synced:
                log.debug(
                    f"unknown user in group {vrcm.user.display_name} {vrcm.user.id}"
                )
                report["groupUnk"] += 1
                if list_unkown:
                    report["unkown"].append([vrcm.user.display_name, vrcm.user.id])

        return report

    @business_event(MemberManagementEvent.MemberLeft)
    async def remove_member(self, event: MemberManagementEvent.MemberLeft):
        if not event.officer:
            log.error(f"officer object is invalid, of{event.member_id}")
            return
        log.debug(f"vrc will remove {event.officer.vrchat_name}")

        group_api = vrchatapi.GroupsApi(self.api_client)
        try:
            t = group_api.kick_group_member(
                group_id=settings.VRC_GROUP_ID,
                user_id=event.officer.vrchat_id,
                async_req=True,
            )
            r = t.get()
            log.debug(
                f"kicked {event.officer.vrchat_name} {event.officer.vrchat_id} {r=}"
            )
            if event.officer.extra == None:
                event.officer.extra = {}
            event.officer.extra["vrcRegStatus"] = (
                VrcUserRegistrationStatus.UNREGISTERED.value
            )
            await event.officer.update()
        except vrchatapi.ApiException as e:
            # log.exception(
            #     f"unable to kick user did{event.officer.id} vrcname`{event.officer.vrchat_name}`{event.officer.vrchat_id}"
            # )
            log.error(
                f"unable to kick did{event.officer.id} vrcname`{event.officer.vrchat_name}`{event.officer.vrchat_id}"
            )
            log.debug(e.body)
