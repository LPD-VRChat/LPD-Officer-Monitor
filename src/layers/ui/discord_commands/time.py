# Settings import
import settings

# Standard
import datetime as dt
from typing import Optional
import logging
import enum

# Community
import discord
from discord.ext import commands
from discord import app_commands as app_cmd

# Custom
import src.layers.business.checks as checks
import src.layers.business.errors as errors
import src.layers.business

from src.layers.business.bl_wrapper import BusinessLayerWrapper
from src.layers.business.extra_functions import (
    get_lpd_member_rank,
    has_role_id,
    is_lpd_member,
    msgbox_confirm,
    send_long,
    now,
    interaction_send_long,
    parse_iso_date,
    interaction_reply,
    interaction_send_str_as_file,
    timedelta_to_nice_string,
)

log = logging.getLogger("lpd-officer-monitor")


class Training(enum.Enum):
    recruit = 0
    senior_officer = 1
    LMT = 2
    SLRT = 3
    Watch_officer = 4


class Time(commands.Cog):
    def __init__(self, bot):
        self.bl_wrapper: BusinessLayerWrapper = bot.bl_wrapper
        self.bot = bot
        self.color = discord.Color.blue()

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command()
    async def time(self, ctx: commands.Context, officer: discord.Member):
        """
        TEMPORARY TEST COMMAND
        """
        await send_long(
            ctx.channel,
            str(
                await self.bl_wrapper.pt_bl.get_patrol_time(
                    officer.id, from_dt=now() - dt.timedelta(days=28), to_dt=now()
                )
            ),
        )

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command()
    async def time_patrols(self, ctx: commands.Context, officer: discord.Member):
        """
        TEMPORARY TEST COMMAND
        """
        await send_long(
            ctx.channel,
            str(
                await self.bl_wrapper.pt_bl.get_patrols(
                    officer.id, from_dt=now() - dt.timedelta(days=28), to_dt=now()
                )
            ),
        )

    @checks.is_admin_bot_channel()
    @checks.is_white_shirt()
    @commands.command()
    async def time_patrol_voices(self, ctx: commands.Context, officer: discord.Member):
        """
        TEMPORARY TEST COMMAND
        """
        await send_long(
            ctx.channel,
            str(
                await self.bl_wrapper.pt_bl.get_patrol_voices(
                    officer.id, from_dt=now() - dt.timedelta(days=28), to_dt=now()
                )
            ),
        )

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(name="time_patrols", description="Returns patrol times")
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    @app_cmd.describe(officer="list the members of this role")
    @app_cmd.describe(days="look up number of days in the past (default=28)")
    @app_cmd.describe(from_date="ISO 8601 format YYYY-MM-DD (days will be ignored)")
    @app_cmd.describe(to_date="ISO 8601 format YYYY-MM-DD (days will be ignored)")
    @app_cmd.describe(full_list="list all the patrols, else list total patrol time")
    async def time_slash(
        self,
        interac: discord.Interaction,
        officer: discord.Member,
        days: int = 28,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        full_list: bool = False,
    ):
        from_dt = now() - dt.timedelta(days=days)
        to_dt = now()
        use_days = True
        match (from_date is None, to_date is None):
            case (True, True):
                pass
            case (False, False):
                try:
                    from_dt = parse_iso_date(from_date)
                except ValueError:
                    await interaction_reply(
                        interac, "invalid date `from_date` argument", ephemeral=True
                    )
                    return
                try:
                    to_dt = parse_iso_date(to_date)
                except ValueError:
                    await interaction_reply(
                        interac, "invalid date `to_date` argument", ephemeral=True
                    )
                    return
                use_days = False
            case (True, False):
                await interaction_reply(
                    interac, "you forgot `to_date` argument", ephemeral=True
                )
                return
            case (False, True):
                await interaction_reply(
                    interac, "you forgot `from_date` argument", ephemeral=True
                )
                return
        await interac.response.defer(ephemeral=False, thinking=True)

        if full_list:
            patrols = await self.bl_wrapper.pt_bl.get_patrols(
                officer.id, from_dt=from_dt, to_dt=to_dt
            )
            results = []
            for p in patrols:
                await p.main_channel.load()  # propably very bad
                results.append(
                    f"{p.start.isoformat(sep=' ', timespec='seconds')}  {str(p.duration())} {'in event' if p.event else 'freeroam'} {p.main_channel.name}"
                )
            result = "\n".join(results)

        else:
            timeDelta = await self.bl_wrapper.pt_bl.get_patrol_time(
                officer.id, from_dt=from_dt, to_dt=to_dt
            )
            if use_days:
                result = f"Patrolling time for {officer.name}[{officer.id}] in last {days} days: "
            else:
                result = f"Patrolling time for {officer.name}[{officer.id}] between {from_dt} and {to_dt} : "
            result += timedelta_to_nice_string(timeDelta)

        await interaction_send_long(
            interac,
            result,
        )

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(name="time_top", description="gives top patrolling times")
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    @app_cmd.describe(days="look up number of days in the past (default=28)")
    @app_cmd.describe(from_date="ISO 8601 format YYYY-MM-DD (days will be ignored)")
    @app_cmd.describe(to_date="ISO 8601 format YYYY-MM-DD (days will be ignored)")
    async def time_top_slash(
        self,
        interac: discord.Interaction,
        days: int = 28,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ):
        from_dt = now() - dt.timedelta(days=days)
        to_dt = now()
        match (from_date is None, to_date is None):
            case (True, True):
                pass
            case (False, False):
                try:
                    from_dt = parse_iso_date(from_date)
                except ValueError:
                    await interaction_reply(
                        interac, "invalid date `from_date` argument", ephemeral=True
                    )
                    return
                try:
                    to_dt = parse_iso_date(to_date)
                except ValueError:
                    await interaction_reply(
                        interac, "invalid date `to_date` argument", ephemeral=True
                    )
                    return
            case (True, False):
                await interaction_reply(
                    interac, "you forgot `to_date` argument", ephemeral=True
                )
                return
            case (False, True):
                await interaction_reply(
                    interac, "you forgot `from_date` argument", ephemeral=True
                )
                return

        await interac.response.defer(ephemeral=False, thinking=True)

        try:
            leaderboard = await self.bl_wrapper.pt_bl.get_top_patrol_time(
                from_dt=from_dt, to_dt=to_dt
            )
        except Exception as e:
            print(e)
            return

        leaderboard_lines = []
        for k, v in leaderboard.items():
            officer_name = await self.bl_wrapper.mm_bl.get_officer_vrcname_from_id(k)
            leaderboard_lines.append(f"{officer_name} = {timedelta_to_nice_string(v)}")

        await interaction_send_long(
            interac,
            "\n".join(leaderboard_lines),
        )

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(
        name="list_promotable_recruits",
        description="List recruits that could be promoted to Officer",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    @app_cmd.describe(days="look up number of days in the past (default=28)")
    @app_cmd.describe(minimum="Minimum hours of patrol time")
    async def list_promotable_recruits(
        self,
        interac: discord.Interaction,
        minimum: int,
        days: int = 28,
    ):
        guild = self.bot.get_guild(settings.SERVER_ID)
        if not guild:
            raise Exception(f"guild {settings.SERVER_ID} is not accessible")

        role = guild.get_role(settings.ROLE_LADDER.recruit.id)
        if role is None:
            raise Exception(
                f"recruit role {settings.ROLE_LADDER.recruit.id} is not accessible"
            )
        from_dt = now() - dt.timedelta(days=days)
        result = await self.bl_wrapper.pt_bl.get_potential_officer_promotion(
            from_dt, minimum
        )
        mentions = " ".join(f"<@{officer.id}>" for officer in result)

        await interaction_reply(
            interac,
            f"Potential promotion to Officer {len(result)}/{len(role.members)}:\n"
            + mentions,
        )

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(
        name="promote_to_officer",
        description="Promote to Officer all mentions in a message",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    @app_cmd.describe(
        message_id_or_link="the message ID or Link where all mentions need to be promoted to Officers"
    )
    async def promote_to_officer(
        self,
        interac: discord.Interaction,
        message_id_or_link: str,
    ):
        # messade_id needs to be str anyways it too big to fit integer discord limits
        guild: discord.Guild = self.bot.get_guild(settings.SERVER_ID)
        if not guild:
            raise Exception(f"guild {settings.SERVER_ID} is not accessible")

        # if only message id we expect message to be in admin bot channel
        if "/" not in message_id_or_link:
            try:
                message_id = int(message_id_or_link)
            except ValueError:
                await interaction_reply(
                    interac,
                    f":red_circle: Invalid int",
                )
                return

            admin_ch = guild.get_channel(settings.ADMIN_BOT_CHANNEL)
            assert isinstance(
                admin_ch, discord.TextChannel
            ), "settings.ADMIN_BOT_CHANNEL is not a TextChannel"
            try:
                prom_msg = await admin_ch.fetch_message(message_id)
            except Exception as e:
                logging.error("Fetch msg error:" + str(e))
                await interaction_reply(
                    interac,
                    f":red_circle: Error while retriving message.\nMake sure it's in <#{settings.ADMIN_BOT_CHANNEL}>",
                )
                return
        else:
            url_chunks = message_id_or_link.split("/")
            if (
                not message_id_or_link.startswith("https://discord.com/channels/")
                or len(url_chunks) != 7
            ):
                await interaction_reply(
                    interac,
                    f":red_circle: Invalid Discord message link",
                )
                return
            try:
                guild_id = int(url_chunks[-3])
                channel_id = int(url_chunks[-2])
                message_id = int(url_chunks[-1])
            except ValueError:
                await interaction_reply(
                    interac,
                    f":red_circle: Invalid ids in Discord message link",
                )
                return
            if guild_id != settings.SERVER_ID:
                await interaction_reply(
                    interac,
                    f":red_circle: Discord message link points to outside Guild/Server",
                )
                return
            ch = guild.get_channel(channel_id)
            assert isinstance(
                ch, discord.TextChannel
            ), "settings.ADMIN_BOT_CHANNEL is not a TextChannel"
            try:
                prom_msg = await ch.fetch_message(message_id)
            except Exception as e:
                logging.error("Fetch msg error:" + str(e))
                await interaction_reply(
                    interac,
                    f":red_circle: Error while retriving message.\nThe bot probably doesn't have access to that channel",
                )
                return

        if len(prom_msg.mentions) == 0:
            await interaction_reply(
                interac,
                f":red_circle: No mention in the message",
            )
            return

        role_rm = guild.get_role(settings.ROLE_LADDER.recruit.id)
        if role_rm is None:
            raise Exception(
                f"recruit role {settings.ROLE_LADDER.recruit.id} is not accessible"
            )
        role_add = guild.get_role(settings.ROLE_LADDER.officer.id)
        if role_add is None:
            raise Exception(
                f"officer role {settings.ROLE_LADDER.officer.id} is not accessible"
            )

        sucess = 0
        error = 0
        for m in prom_msg.mentions:
            if not isinstance(m, discord.Member):
                log.error(f"User {m.name}[{m.id}] not in the guild/server")
                error += 1
                continue
            if role_rm not in m.roles:
                log.warn(f"skiped non recruit {m.name}")
                error += 1
            else:
                try:
                    await m.add_roles(
                        role_add,
                        reason="bot promotion to officer",
                        atomic=True,
                    )
                    await m.remove_roles(
                        role_rm,
                        reason="bot promotion to officer",
                        atomic=True,
                    )
                except Exception as e:
                    if isinstance(e, discord.errors.Forbidden):
                        await interaction_reply(
                            interac,
                            ":red_circle: Bot permission issue!",
                        )
                        log.exception(
                            f"Bot role is probably bellow officer and cannot change roles\n{e}"
                        )
                        return
                    log.exception(f"Failed to promote officer {m.name}[{m.id}]\n{e}")
                    error += 1
                    continue
                sucess += 1

        await interaction_reply(
            interac,
            f"Successfully promoted {sucess}/{len(prom_msg.mentions)}. Ignored or errors = {error}\n",
        )

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(
        name="remove_inactive_cadets",
        description="Remove inactive cadet for the amount of days",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    @app_cmd.describe(
        inactive_days_required="amount of days a cadet need to be inactive to be yeeted (default=28)"
    )
    async def remove_inactive_cadets(
        self,
        interac: discord.Interaction,
        inactive_days_required: int = 28,
    ):
        guild = self.bot.get_guild(settings.SERVER_ID)
        if not guild:
            raise Exception(f"guild {settings.SERVER_ID} is not accessible")

        role = guild.get_role(settings.ROLE_LADDER.cadet.id)
        if role is None:
            raise Exception(
                f"cadet role {settings.ROLE_LADDER.cadet.id} is not accessible"
            )

        await interac.response.defer(ephemeral=False, thinking=True)
        date_from = dt.datetime.now() - dt.timedelta(days=inactive_days_required)
        inactives = await self.bl_wrapper.pt_bl.get_inactive_cadets(date_from, 1)
        message = f"Inactive cadets {len(inactives)}:\n"
        message += "\n".join([f"<@{o.id}>" for o in inactives])

        await interaction_send_long(interac, message)
        if len(inactives) == 0:
            return

        if not await msgbox_confirm(
            interac,
            message="Do you want to remove all those inactive cadets",
        ):
            return

        r = await self.bl_wrapper.pt_bl.remove_cadet(inactives)
        await interaction_reply(
            interac,
            content="All cadets have been sacrified successfully"
            if r
            else ":red_circle: Some errors happened, please check the logs!!!",
        )

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(
        name="list_loa",
        description="List ongoing Leave Of Absence",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    async def list_loa(self, interac: discord.Interaction):
        entries = await self.bl_wrapper.loa_bl.list_loa()
        output = "discord_id,vrchat_name,start,end\n"

        def csv_quote_escape(input: str):
            return input.replace('"', '""')

        for entry in entries:
            await entry.officer.load()  # to get vrchat_name, else only id is defined
            # id is set as string in csv because it's too long. libreoffice transform to 1.2e25 notation
            output += f'"{entry.officer.id}","{csv_quote_escape(entry.officer.vrchat_name)}",{entry.start.isoformat()},{entry.end.isoformat()}\n'
        await interaction_send_str_as_file(
            interac, output, f"loa_entries.csv", "LOA entries"
        )

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(
        name="mark_inactive",
        description="Mark officers as inactive",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    async def mark_inactive(self, interac: discord.Interaction):
        await interac.response.defer(ephemeral=False, thinking=True)
        date_from = dt.datetime.now() - dt.timedelta(days=settings.MAX_INACTIVE_DAYS)
        officers_bellow_time = (
            await self.bl_wrapper.pt_bl.get_officer_bellow_patrol_time(
                date_from, settings.MIN_ACTIVITY_MINUTES / 60
            )
        )
        loas = await self.bl_wrapper.loa_bl.list_loa()
        renews = await self.bl_wrapper.loa_bl.list_renewed(date_from)
        inactives = await self.bl_wrapper.loa_bl.process_inactives(
            officers_bellow_time, loas, renews
        )

        message = "Inactive officers:\n"
        message += "\n".join([f"<@{o.id}>" for o in inactives])

        await interaction_send_long(interac, message)

        if not await msgbox_confirm(
            interac,
            message="Do you want to mark all those officers as inactive",
        ):
            return

        guild = self.bot.get_guild(settings.SERVER_ID)
        if not guild:
            raise Exception(f"guild {settings.SERVER_ID} is not accessible")
        role_inactive = guild.get_role(settings.INACTIVE_ROLE)
        if role_inactive is None:
            raise Exception(f"inactive role {settings.INACTIVE_ROLE} is not accessible")

        for officer in inactives:
            member = guild.get_member(officer.id)
            if not member:
                log.error(f"officer {officer.id} invalid member!!!")
                continue
            await member.add_roles(role_inactive, reason="bot mark_inactive")
        await interaction_reply(interac, content="Done")

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(
        name="renew",
        description="renew an officers",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    async def renew(self, interac: discord.Interaction, officer: discord.Member):
        if not is_lpd_member(officer):
            await interaction_reply(
                interac, "This discord member is not an LPD officer"
            )
            return

        await self.bl_wrapper.loa_bl.create_renew(officer.id, interac.user.id)
        await interaction_reply(interac, "Renewal Done")

    @checks.is_admin_bot_channel(True)
    @checks.is_white_shirt(True)
    @app_cmd.command(
        name="list_renewals",
        description="List all renewawls of an officers",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    async def list_renewals(
        self, interac: discord.Interaction, officer: discord.Member
    ):
        if not is_lpd_member(officer):
            await interaction_reply(
                interac,
                "This discord member is not an LPD officer",
            )
            return

        ren = await self.bl_wrapper.loa_bl.list_renew(officer.id)

        if len(ren) == 0:
            await interaction_reply(
                interac,
                f"Renewal ",
            )
        await interaction_reply(
            interac,
            f"Renewal :\n" + "\n".join([r.timestamp.isoformat() for r in ren]),
        )

    @checks.is_recruiter_bot_channel(True)
    @checks.app_cmd_check_any(
        checks.is_recruiter(True),
        checks.is_white_shirt(True),
    )
    @app_cmd.command(
        name="give_cadet_role",
        description="give_cadet_role",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    async def give_cadet_role(
        self, interac: discord.Interaction, member: discord.Member
    ):
        lpd_role = discord.Object(settings.LPD_ROLE)
        cadet_role = discord.Object(settings.ROLE_LADDER.cadet.id)
        await member.add_roles(lpd_role, cadet_role, reason="bot promote cadet")
        await interaction_reply(interac, f"<@{member.id}> `{member.id}` is now a cadet")

    @checks.is_team_bot_channel(True)
    @checks.app_cmd_check_any(
        checks.is_any_trainer(True),
        checks.is_white_shirt(True),
    )
    @app_cmd.command(
        name="give_trained_role",
        description="give_trained_role",
    )
    @app_cmd.guilds(discord.Object(id=settings.SERVER_ID))
    @app_cmd.default_permissions(administrator=True)
    async def give_trained_role(
        self,
        interac: discord.Interaction,
        member: discord.Member,
        training: Training,
    ):
        rank = get_lpd_member_rank(interac.user)
        if not rank:
            log.error(f"officer {interac.user.id} does not have a rank")
            raise PermissionError("could not get rank")
            return
        if not rank.is_white_shirt:  # chk right trainer
            match training:
                case Training.recruit | Training.senior_officer:
                    if not has_role_id(interac.user, settings.TRAINER_ROLE):
                        await interaction_reply(
                            interac,
                            f":red_circle: failed to promote <@{member.id}> for `{training.name}`, you are not a trainer",
                        )
                        return
                case Training.LMT:
                    if not has_role_id(interac.user, settings.LMT_TRAINER_ROLE):
                        await interaction_reply(
                            interac,
                            f":red_circle: failed to promote <@{member.id}> for `{training.name}`, you are not an LMT trainer",
                        )
                        return
                case Training.SLRT:
                    if not has_role_id(interac.user, settings.SLRT_TRAINER_ROLE):
                        await interaction_reply(
                            interac,
                            f":red_circle: failed to promote <@{member.id}> for `{training.name}`, you are not an SLRT trainer",
                        )
                        return
                case Training.Watch_officer:
                    if not has_role_id(interac.user, settings.PRISON_TRAINER_ROLE):
                        await interaction_reply(
                            interac,
                            f":red_circle: failed to promote <@{member.id}> for `{training.name}`, you are not a Prison trainer",
                        )
                        return
                case _:
                    await interaction_reply(interac, ":red_circle: invalid training.")
                    log.error(f"invalid training {training.value}")
                    return

        match training:
            case Training.recruit:
                await member.add_roles(
                    discord.Object(settings.ROLE_LADDER.recruit.id),
                    reason="bot trained recruit",
                )
                await member.remove_roles(
                    discord.Object(settings.ROLE_LADDER.cadet.id),
                    reason="bot trained recruit",
                )
            case Training.senior_officer:
                await member.add_roles(
                    discord.Object(settings.ROLE_LADDER.senior_officer.id),
                    reason="bot trained senior_officer",
                )
                await member.remove_roles(
                    discord.Object(settings.ROLE_LADDER.officer.id),
                    reason="bot trained senior_officer",
                )
            case Training.LMT:
                await member.add_roles(
                    discord.Object(settings.LMT_TRAINED_ROLE),
                    reason="bot trained LMT",
                )
            case Training.SLRT:
                await member.add_roles(
                    discord.Object(settings.SLRT_TRAINED_ROLE),
                    reason="bot trained SLRT",
                )
            case Training.Watch_officer:
                await member.add_roles(
                    discord.Object(settings.WATCH_OFFICER_ROLE),
                    reason="bot trained Watch_officer",
                )
            case _:
                await interaction_reply(interac, ":red_circle: invalid training.")
                log.error(f"invalid training {training.value}")
                return
        await interaction_reply(
            interac, f"<@{member.id}> is trained for `{training.name}`"
        )


async def setup(bot):
    await bot.add_cog(Time(bot))
