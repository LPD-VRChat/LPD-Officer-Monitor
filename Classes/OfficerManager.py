# ====================
# Imports
# ====================

# Standard
import asyncio
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Community
import aiomysql
import discord.errors as discord_errors
from pymysql import err as mysql_errors
import discord
from discord.ext import tasks

# Mine
from Classes.Officer import Officer
from Classes.errors import MemberNotFoundError
from Classes.extra_functions import handle_error, role_id_index
from Classes.extra_functions import ts_print as print


class OfficerManager:
    def __init__(self, all_officer_ids, bot, run_before_officer_removal=None):
        self.bot = bot
        self._before_officer_removal = run_before_officer_removal
        self.all_officer_ids = all_officer_ids

        # Get the guild
        self.guild = bot.get_guild(bot.settings["Server_ID"])
        if self.guild is None:
            print("ERROR Guild with ID", bot.settings["Server_ID"], "not found")
            print("Shutting down...")
            exit()

        # Get all monitored channels
        self.all_monitored_channels = [
            c.id
            for c in self.guild.channels
            if c.category
            not in bot.settings["monitored_channels"]["ignored_categories"]
            and isinstance(c, discord.channel.TextChannel)
        ]

        # Add all the officers to the list
        self._all_officers = dict()
        self._officers_needing_removal = []
        print("Adding all the officers to the Officer Manager")
        for officer_id in all_officer_ids:
            try:
                new_officer = Officer(officer_id, bot)
                self._all_officers[officer_id] = new_officer
                print(
                    f"Added {new_officer.member.name}#{new_officer.member.discriminator} to the Officer Manager."
                )

                # Check to see if the officer is in an on duty VC, and if so, put them on duty, put a message in stdout and increment a counter
                if new_officer.member.voice is not None:
                    if (
                        new_officer.member.voice.channel.category_id
                        == self.bot.settings["on_duty_category"]
                    ):
                        print(
                            f"Note: {new_officer.member.name}#{new_officer.member.discriminator} is on duty. Starting their time now..."
                        )
                        new_officer.go_on_duty()

            except MemberNotFoundError:
                print(
                    f"The officer with the ID {officer_id} was not found in the server. The officer will be removed in a moment."
                )
                self._officers_needing_removal.append(officer_id)

        print(f"Officers needing removal: {self._officers_needing_removal}")

        # Set up the automatically running code
        self.loop.start()
        self.loop.change_interval(
            minutes=bot.settings["sleep_time_between_officer_checks"]
        )
        self.loa_loop.start()

    @classmethod
    async def start(cls, bot, run_before_officer_removal=None):

        # Fetch all the officers from the database
        try:
            result = await bot.sql.request("SELECT officer_id FROM Officers")

        except Exception as error:
            print("ERROR failed to fetch officers from database:")
            print(error)
            print("Shutting down...")
            exit()

        return cls(
            (x[0] for x in result),
            bot,
            run_before_officer_removal=run_before_officer_removal,
        )

    # =====================
    #    Loop
    # =====================

    @tasks.loop(minutes=60)
    async def loop(self):
        print("Running officer check loop in officer_manager")

        try:
            # Add missing officers
            for member in self.all_server_members_in_LPD:
                if not self.is_monitored(member.id):
                    await self.create_officer(
                        member.id, issue="was not caught by on_member_update event"
                    )

            # Remove extra users from the officer_monitor
            for member_id in self._all_officers:

                member = self.guild.get_member(member_id)

                if member is None:
                    await self.remove_officer(
                        member_id, reason="this person was not found in the server"
                    )
                    continue

                if self.is_officer(member) is False:
                    await self.remove_officer(
                        member_id,
                        reason="this person is in the server but does no longer have an LPD Officer role",
                    )
                    continue

            # Remove the users in the remove list
            for officer_id in self._officers_needing_removal:
                await self.remove_officer(
                    officer_id, reason="this person was not found in the server."
                )

            # Build the list of LPD Ranks, for general availability
            self.all_lpd_ranks = [
                self.guild.get_role(role_id)
                for role_id in role_id_index(self.bot.settings)
            ]

        except Exception as error:
            print(error)
            print(traceback.format_exc())

    @tasks.loop(hours=1)
    async def loa_loop(self):
        await self.get_loa()

    # =====================
    #    modify officers
    # =====================

    def get_officer(self, officer_id: int) -> Officer:
        """Returns Officer object from Officer ID"""

        try:
            return self._all_officers[officer_id]
        except KeyError:
            return None

    async def create_officer(self, officer_id, issue=None):
        """Attempts to create Officer object from given Officer ID"""

        # Add the officer to the database
        try:
            try:
                await self.bot.sql.request(
                    "INSERT INTO Officers(officer_id, started_monitoring_time) Values (%s, %s)",
                    (officer_id, datetime.utcnow()),
                )
            except mysql_errors.IntegrityError as error:
                print(repr(error.args))
                return None
        except Exception as error:
            await handle_error(
                self.bot,
                f"**Failed to add the officer with the ID {officer_id} to the database.**",
                traceback.format_exc(),
            )
            return None

        # Create the officer
        new_officer = Officer(officer_id, self.bot)

        # Add the officer to the _all_officers list
        self._all_officers[officer_id] = new_officer

        # Print
        msg_string = (
            "INFO: "
            + new_officer.display_name
            + " ("
            + str(new_officer.id)
            + ") has been added to the LPD Officer Monitor"
        )
        if issue is None:
            msg_string += " the correct way."
        else:
            msg_string += " but " + str(issue)
        print(msg_string)
        channel = self.bot.get_channel(self.bot.settings["error_log_channel"])
        await channel.send(msg_string)

        # Return the officer
        return new_officer

    async def remove_officer(self, officer_id, reason=None, display_name=None):

        # Run the function that needs to run before the officer removal
        try:
            if self._before_officer_removal:
                await self._before_officer_removal(self.bot, officer_id)
        except Exception:
            await handle_error(
                self.bot,
                "Error encountered in before_officer_removal function",
                traceback.format_exc(),
            )

        # Get display name for the Officer to be removed
        if display_name == None:
            member_name = str(officer_id)
        else:
            member_name = f"{display_name} ({officer_id})"

        await self.bot.sql.request(
            "DELETE FROM MessageActivityLog WHERE officer_id = %s", (officer_id)
        )
        await self.bot.sql.request(
            "DELETE FROM TimeLog WHERE officer_id = %s", (officer_id)
        )
        await self.bot.sql.request(
            "DELETE FROM LeaveTimes WHERE officer_id = %s", (officer_id)
        )
        await self.bot.sql.request(
            "DELETE FROM Officers WHERE officer_id = %s", (officer_id)
        )

        # Remove the officer from the officer list
        try:
            del self._all_officers[officer_id]
        except KeyError:
            print(
                f"ERROR: Officer {officer_id} was not in the Monitored list of Officers"
            )

        msg_string = (
            "INFO: " + member_name + " has been removed from the LPD Officer Monitor"
        )
        if reason is not None:
            msg_string += " because " + str(reason)
        print(msg_string)
        channel = self.bot.get_channel(self.bot.settings["error_log_channel"])
        await channel.send(msg_string)

    # ====================
    #    check officers
    # ====================

    async def get_most_active_officers(
        self,
        from_datetime: datetime,
        to_datetime: datetime,
        limit: Optional[int] = None,
        include_no_activity: bool = False,
    ):
        """
        Returns list of most active officers between given dates, up to optionally specified limit.

        This can both be used when the most active officers are needed or if you need to get all
        officers and how active they have been over a specific amount of time.
        """

        db_request = (
            """
            SELECT O.officer_id, SUM(TIMESTAMPDIFF(SECOND, TL.start_time, TL.end_time)) AS "patrol_length"
            FROM Officers O
                LEFT JOIN TimeLog TL
                    ON O.officer_id = TL.officer_id
            WHERE
                (TL.end_time > %s AND TL.end_time < %s)
            """
            + ("OR TL.end_time IS NULL\n" if include_no_activity else "")
            + """
            GROUP BY O.officer_id
            ORDER BY patrol_length DESC
            """
        )
        arg_list: List[Any] = [from_datetime, to_datetime]

        if limit:
            db_request += "\nLIMIT %s"
            arg_list.append(limit)

        return await self.bot.sql.request(db_request, arg_list)

    async def get_officer_renew_dates(self) -> Dict[int, datetime]:
        """
        Returns a dictionary with the officer id as key, and then when their time was last
        renewed or join date as the value, witch ever one is higher.
        """
        data = await self.bot.sql.request(
            "SELECT officer_id, renewed_time, started_monitoring_time FROM Officers"
        )
        return {d[0]: max(d[1], d[2]) for d in data}

    def is_officer(self, member):
        """Returns true if specified member object has and of the LPD roles"""

        if member is None:
            return False
        all_lpd_ranks = [x["id"] for x in self.bot.settings["role_ladder"]]
        all_lpd_ranks.append(self.bot.settings["lpd_role"])
        for role in member.roles:
            if role.id in all_lpd_ranks:
                return True
        return False

    def is_monitored(self, member_id: int) -> bool:
        """Returns true if specified member ID matches an officer ID in memory"""

        return member_id in self._all_officers.keys()

    @property
    def all_server_members_in_LPD(self):
        return [m for m in self.guild.members if self.is_officer(m)]

    @property
    def all_server_members_not_in_LPD(self):
        return [m for m in self.guild.members if not self.is_officer(m)]

    @property
    def all_officers(self):
        return self._all_officers

    # ====================
    #   other functions
    # ====================

    def get_settings_role(self, name_id):
        """Returns a role object for given name_id"""

        for role in self.bot.settings["role_ladder"]:
            if role["name_id"] == name_id:
                return role
        raise ValueError(f"{name_id} not found in bot.settings")

    async def remove_loa(self, request_id):
        """
        Delete the specified Leave of Absence
        """

        await self.bot.sql.request(
            "DELETE FROM LeaveTimes WHERE request_id = %s", (request_id)
        )

    async def get_loa(self):
        loa_entries = await self.bot.sql.request(
            "SELECT officer_id, date(date_start), date(date_end), reason, request_id FROM LeaveTimes"
        )

        loa_channel = self.bot.get_channel(
            self.bot.settings["leave_of_absence_channel"]
        )

        for entry in loa_entries:
            if entry[2] > datetime.utcnow().date():
                pass
            else:
                old_msg_id = entry[4]
                old_msg = await loa_channel.fetch_message(old_msg_id)
                await old_msg.delete()

                await self.remove_loa(str(entry[4]))
                templist = list(loa_entries)
                templist.remove(entry)
                loa_entries = tuple(templist)

        return loa_entries
