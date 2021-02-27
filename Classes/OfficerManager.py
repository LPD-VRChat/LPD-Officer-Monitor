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
        self._all_officers = []
        self._officers_needing_removal = []
        print("Adding all the officers to the Officer Manager")
        for officer_id in all_officer_ids:
            try:
                new_officer = Officer(officer_id, bot)
                self._all_officers.append(new_officer)
                print(
                    f"Added {new_officer.member.name}#{new_officer.member.discriminator} to the Officer Manager."
                )
            except MemberNotFoundError:
                print(
                    f"The officer with the ID {officer_id} was not found in the server. The officer will be removed in a moment."
                )
                self._officers_needing_removal.append(officer_id)
        print(f"Officers needing removal: {self._officers_needing_removal}")

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

        result = await self.bot.sql.request(query, args)
        return result

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
            for officer_member in self._all_officers:
                member_id = officer_member.id

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

        except Exception as error:
            print(error)
            print(traceback.format_exc())

        await asyncio.sleep(self.bot.settings["sleep_time_between_officer_checks"])

    # =====================
    #    modify officers
    # =====================

    def get_officer(self, officer_id):
        """Returns Officer object from Officer ID"""

        for officer in self._all_officers:
            if officer.id == officer_id:
                return officer
        return None

    async def create_officer(self, officer_id, issue=None):
        """Attempts to create Officer object from given Officer ID"""

        # Add the officer to the database
        try:
            try:
                await self.bot.sql.request(
                    "INSERT INTO Officers(officer_id, started_monitoring_time) Values (%s, %s)",
                    (officer_id, datetime.now(timezone.utc)),
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
        self._all_officers.append(new_officer)

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

    async def remove_officer(self, officer_id, reason=None):

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

        await self.bot.sql.request(
            "DELETE FROM MessageActivityLog WHERE officer_id = %s", (officer_id)
        )
        await self.bot.sql.request(
            "DELETE FROM TimeLog WHERE officer_id = %s", (officer_id)
        )
        await self.bot.sql.request(
            "DELETE FROM Officers WHERE officer_id = %s", (officer_id)
        )

        # Remove the officer from the officer list
        i = 0
        while i < len(self._all_officers):
            if self._all_officers[i].id == officer_id:
                del self._all_officers[i]
            else:
                i += 1

        msg_string = (
            "WARNING: "
            + str(officer_id)
            + " has been removed from the LPD Officer Monitor"
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

    def is_monitored(self, member_id):
        """Returns true if specified member ID matches an officer ID in memory"""

        for officer in self._all_officers:
            if officer.id == member_id:
                return True
        return False

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
