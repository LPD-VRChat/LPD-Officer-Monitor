# ====================
# Imports
# ====================

# Standard
import asyncio
import traceback
from datetime import datetime, timezone

# Community
import aiomysql
import discord.errors as discord_errors
from pymysql import err as mysql_errors
import discord
from discord.ext import tasks

# Mine
from Classes.Officer import Officer
from Classes.errors import MemberNotFoundError
from Classes.extra_functions import handle_error


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
        self._number_officers_on_duty_at_launch = 0
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
                        self._number_officers_on_duty_at_launch += 1

            except MemberNotFoundError:
                print(
                    f"The officer with the ID {officer_id} was not found in the server. The officer will be removed in a moment."
                )
                self._officers_needing_removal.append(officer_id)

        print(f"Officers needing removal: {self._officers_needing_removal}")

        # If there were officers on duty when the OfficerManager started, put a warning in stdout
        if self._number_officers_on_duty_at_launch > 1:
            pretty_text = f"were {self._number_officers_on_duty_at_launch} officers"

        if self._number_officers_on_duty_at_launch == 1:
            pretty_text = f"was {self._number_officers_on_duty_at_launch} officer"

        if self._number_officers_on_duty_at_launch > 0:
            print(
                f"WARNING: It looks like there {pretty_text} on duty when the Officer Manager was started... This is indicative of a bot crash. Any on-duty time not logged before the bot crashed will not be logged. Their time has been restarted. (remove this code when the clean shutdown is implemented)"
            )

        # Set up the automatically running code
        bot.loop.create_task(self.loop())

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

    async def send_db_request(self, query, args=None):
        """This function is being deprecated in favor of self.bot.sql.request()"""
        return await self.bot.sql.request(query, args)

    # =====================
    #    Loop
    # =====================

    async def loop(self):
        # Wait until everything is ready
        while not self.bot.everything_ready:
            await asyncio.sleep(2)

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
                        display_name=member.display_name,
                    )
                    continue

            # Remove the users in the remove list
            for officer_id in self._officers_needing_removal:
                await self.remove_officer(
                    officer_id, reason="this person was not found in the server."
                )

        except Exception as error:
            print(error)
            print(traceback.format_exc())

        await asyncio.sleep(self.bot.settings["sleep_time_between_officer_checks"])

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
            "DEBUG: "
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
            "WARNING: " + member_name + " has been removed from the LPD Officer Monitor"
        )
        if reason is not None:
            msg_string += " because " + str(reason)
        print(msg_string)
        channel = self.bot.get_channel(self.bot.settings["error_log_channel"])
        await channel.send(msg_string)

    # ====================
    #    check officers
    # ====================

    async def get_most_active_officers(self, from_datetime, to_datetime, limit=None):
        """Returns list of most active officers between given dates, up to optionally specified limit"""

        db_request = """
            SELECT officer_id, SUM(TIMESTAMPDIFF(SECOND, start_time, end_time)) AS "patrol_length"
            FROM TimeLog
            WHERE end_time > %s AND end_time < %s
            GROUP BY officer_id
            ORDER BY patrol_length DESC
            """
        arg_list = [from_datetime, to_datetime]

        if limit:
            db_request += "\nLIMIT %s"
            arg_list.append(limit)

        return await self.bot.sql.request(db_request, arg_list)

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
        return [m for m in self.guild.members if self.is_officer(m)]

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

        await self.send_db_request(
            "DELETE FROM LeaveTimes WHERE request_id = %s", (request_id)
        )

    async def get_loa(self):
        loa_entries = await self.send_db_request(
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

    @tasks.loop(hours=1)
    async def get_loa_hourly(self):
        await self.get_loa()
