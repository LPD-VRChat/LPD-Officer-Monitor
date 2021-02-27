# ====================
# Imports
# ====================

# Standard
import asyncio
import math
import time
from datetime import datetime
import datetime as dt

# Community
from discord import Member
from Classes.errors import MemberNotFoundError

# Mine
import Classes.extra_functions as ef


class Officer:
    def __init__(self, user_id, bot):
        self.bot = bot
        self.member = bot.get_guild(bot.settings["Server_ID"]).get_member(user_id)
        if self.member == None:
            raise MemberNotFoundError()

        self._on_duty_start_time = None
        self.is_on_duty = False

    def go_on_duty(self):

        print(f"{self.discord_name} is going on duty")

        # Print an error if the user is going on duty even though he is already on duty
        if self.is_on_duty is True:
            print("WARNING A user is going on duty even though he is already on duty")
            return

        # Start counting the officers time
        self._on_duty_start_time = time.time()
        self.is_on_duty = True

    async def go_off_duty(self):

        print(f"{self.discord_name} is going off duty")

        # Print an error if the user is going off duty even though he is already off duty
        if self.is_on_duty is False:
            print("WARNING A user is going off duty even though he isn't on duty")
            return

        # Calculate the on duty time and store it
        await self.log_time(self._on_duty_start_time, time.time())

        # Set the variables
        self._on_duty_start_time = None
        self.is_on_duty = False

    async def remove(self):

        # Remove itself
        await self.bot.officer_manager.remove_officer(self.id)

    async def process_loa(self, message):
        try:
            date_range = message.content.split(":")[0]
            date_a = date_range.split("-")[0]
            date_b = date_range.split("-")[1]
            date_start = ["", "", ""]
            date_end = ["", "", ""]
            date_start[0] = date_a.split("/")[0].strip()
            date_start[1] = date_a.split("/")[1].strip()
            date_start[2] = date_a.split("/")[2].strip()
            date_end[0] = date_b.split("/")[0].strip()
            date_end[1] = date_b.split("/")[1].strip()
            date_end[2] = date_b.split("/")[2].strip()
            reason = message.content.split(":")[1].strip()
            months = {
                "JAN": 1,
                "FEB": 2,
                "MAR": 3,
                "APR": 4,
                "MAY": 5,
                "JUN": 6,
                "JUL": 7,
                "AUG": 8,
                "SEP": 9,
                "OCT": 10,
                "NOV": 11,
                "DEC": 12,
            }
            int(date_start[0])
            int(date_end[0])

            date_start[1] = date_start[1].upper()[0:3]
            date_start[1] = months[date_start[1]]
            date_end[1] = date_end[1].upper()[0:3]
            date_end[1] = months[date_end[1]]

        except (TypeError, ValueError, KeyError, IndexError):
            # If all of that failed, let the user know with an autodeleting message
            await message.channel.send(
                message.author.mention
                + " Please use correct formatting: 21/July/2020 - 21/August/2020: Reason.",
                delete_after=10,
            )
            await message.delete()
            return

        date_start = [int(i) for i in date_start]
        date_end = [int(i) for i in date_end]

        if (
            date_start[1] < 1
            or date_start[1] > 12
            or date_end[1] < 1
            or date_end[1] > 12
        ):
            # If the month isn't 1-12, let the user know they dumb
            await message.channel.send(
                message.author.mention + " There are only 12 months in a year.",
                delete_after=10,
            )
            await message.delete()
            return

        # Convert our separate data into a usable datetime
        date_start_complex = (
            str(date_start[0]) + "/" + str(date_start[1]) + "/" + str(date_start[2])
        )
        date_end_complex = (
            str(date_end[0]) + "/" + str(date_end[1]) + "/" + str(date_end[2])
        )

        try:
            date_start = dt.datetime.strptime(date_start_complex, "%d/%m/%Y")
            date_end = dt.datetime.strptime(date_end_complex, "%d/%m/%Y")
        except (ValueError, TypeError):
            await message.channel.send(
                message.author.mention
                + " There was a problem with your day. Please use a valid day number.",
                delete_after=10,
            )
            await message.delete()
            return

        if date_end > date_start + dt.timedelta(
            weeks=+12
        ) or date_end < date_start + dt.timedelta(weeks=+3):
            # If more than 12 week LOA, inform user
            await message.channel.send(
                message.author.mention
                + " Leaves of Absence are limited to 3-12 weeks. For longer times, please contact a White Shirt (Lieutenant or Above).",
                delete_after=10,
            )
            await message.delete()
            return

        # Fire the script to save the entry
        request_id = message.id
        old_messages = await self.bot.officer_manager.send_db_request(
            "SELECT request_id FROM LeaveTimes WHERE officer_id = %s", self.id
        )

        if len(old_messages) == 0:
            pass
        else:
            ctx = await self.bot.get_context(message)
            for old_msg_id in old_messages[0]:
                old_msg = await ctx.fetch_message(old_msg_id)
                await old_msg.delete()

        await self.save_loa(date_start, date_end, reason, request_id)
        await message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    async def save_loa(self, date_start, date_end, reason, request_id):
        """
        Pass all 5 required fields to save_loa()
        If record with matching officer_id is found,
        record will be updated with new dates and reason.
        """

        # Delete any existing entries
        await self.bot.officer_manager.send_db_request(
            "DELETE FROM LeaveTimes WHERE officer_id = %s", self.id
        )

        # Save the new entry
        await self.bot.officer_manager.send_db_request(
            "REPLACE INTO `LeaveTimes` (`officer_id`,`date_start`,`date_end`,`reason`,`request_id`) VALUES (%s, %s, %s, %s, %s)",
            (self.id, date_start, date_end, reason, request_id),
        )

    # ====================
    # properties
    # ====================

    # External functions

    @property
    def is_white_shirt(self):
        return self._has_role(*self._get_roles_with_tag("is_white_shirt"))

    @property
    def is_admin(self):
        return self._has_role(*self._get_roles_with_tag("is_admin"))

    @property
    def is_recruiter(self):
        return self._has_role(self.bot.settings["recruiter_role"])

    @property
    def is_trainer(self):
        return self._has_role(self.bot.settings["trainer_role"])

    @property
    def is_slrt_trainer(self):
        return self._has_role(self.bot.settings["slrt_trainer_role"])

    @property
    def is_slrt_trained(self):
        return not self._has_role(self.bot.settings["slrt_trained_role"])

    @property
    def is_dev_member(self):
        return self._has_role(self.bot.settings["dev_team_role"])

    # Often used member functions

    @property
    def discord_name(self):
        return f"{self.member.name}#{self.member.discriminator}"

    @property
    def mention(self):
        return self.member.mention

    @property
    def display_name(self):
        return self.member.display_name

    @property
    def id(self):
        return self.member.id

    # Internal functions

    def _has_role(self, *role_ids):
        for role in self.member.roles:
            if role.id in role_ids:
                return True
        return False

    def _get_roles_with_tag(self, role_tag):
        return tuple(
            x["id"]
            for x in self.bot.settings["role_ladder"]
            if role_tag in x and x[role_tag] == True
        )

    # ====================
    # On Duty Activity
    # ====================

    # External functions

    async def log_time(self, start_time, end_time):

        string_start_time = datetime.fromtimestamp(math.floor(start_time)).strftime(
            self.bot.settings["db_time_format"]
        )
        string_end_time = datetime.fromtimestamp(math.floor(end_time)).strftime(
            self.bot.settings["db_time_format"]
        )

        print(
            "DEBUG Time logged for "
            + self.discord_name
            + ": "
            + string_start_time
            + " - "
            + string_end_time
            + " Seconds: "
            + str(math.floor(end_time - start_time))
        )

        await self.bot.officer_manager.send_db_request(
            "INSERT INTO TimeLog(officer_id, start_time, end_time) VALUES (%s, %s, %s)",
            (self.id, string_start_time, string_end_time),
        )

    async def get_time(self, from_datetime_object, to_datetime_object):
        # Convert the datetime objects into strings the database can understand
        from_db_time = from_datetime_object.strftime(
            self.bot.settings["db_time_format"]
        )
        to_db_time = to_datetime_object.strftime(self.bot.settings["db_time_format"])

        # Execute the query to get the time information
        result = await self.bot.officer_manager.send_db_request(
            """
            SELECT SUM(TIMESTAMPDIFF(SECOND, start_time, end_time)) AS 'Time'
            FROM TimeLog
            WHERE
                officer_id = %s AND
                (start_time > %s AND start_time < %s)
            """,
            (str(self.id), from_db_time, to_db_time),
        )

        # Make sure the function will return a number even though the user has never gone on duty
        if result == None:
            return 0
        else:
            return result[0][0]

    async def get_full_time(self, from_datetime_object, to_datetime_object):

        # Execute the query to get the time information
        result = await self.bot.officer_manager.send_db_request(
            """
            SELECT start_time, end_time, TIMESTAMPDIFF(SECOND, start_time, end_time) AS 'duration'
            FROM TimeLog
            WHERE
                officer_id = %s AND
                (start_time > %s AND start_time < %s)
            """,
            (self.id, from_datetime_object, to_datetime_object),
        )

        # Return the result
        return result

    # ====================
    # Message Activity
    # ====================

    # External functions

    async def get_last_activity(self, counted_channel_ids):
        """
        This functions returns the last active date for an officer,
        the channels that are to be counted and how many days you
        want to look back are passed into the function.
        """
        result = await self._get_all_activity(counted_channel_ids)

        if result == None:
            return None
        max_result = max(result, key=lambda x: time.mktime(x[3].timetuple()))
        return self._create_activity_dict(max_result)

    async def get_all_activity(self, counted_channel_ids):
        """
        This functions returns the last message times for an officer,
        the channels that are to be counted are passed into the function.
        """
        result = await self._get_all_activity(counted_channel_ids)

        if not result:
            return None
        return tuple(self._create_activity_dict(x) for x in result)

    async def log_message_activity(self, msg, send_time=None):

        # Set the send_time if it was not passed in, this was in
        # the kwargs but their it only ran once and gave the same
        # time every single time the function was run.
        if send_time == None:
            send_time = math.floor(time.time())

        # Make a string from the send_time the database can understand
        string_send_time = datetime.fromtimestamp(math.floor(send_time)).strftime(
            self.bot.settings["db_time_format"]
        )

        # Get the row ID for the last activity in the channel
        row_id = await self.bot.officer_manager.send_db_request(
            "SELECT entry_number FROM MessageActivityLog WHERE officer_id = %s AND channel_id = %s",
            (self.id, msg.channel.id),
        )

        # Insert the data into the database
        if row_id:
            row_id = row_id[0][0]
            await self.bot.officer_manager.send_db_request(
                "UPDATE MessageActivityLog SET message_id = %s, send_time = %s WHERE entry_number = %s",
                (msg.id, string_send_time, row_id),
            )
        else:
            await self.bot.officer_manager.send_db_request(
                "INSERT INTO MessageActivityLog(message_id, channel_id, officer_id, send_time) VALUES (%s, %s, %s, %s)",
                (msg.id, msg.channel.id, self.id, string_send_time),
            )

    # Internal functions

    def _create_activity_dict(self, activity_tuple):
        return {
            "officer_id": activity_tuple[0],
            "channel_id": activity_tuple[1],
            "message_id": activity_tuple[2],
            "time": activity_tuple[3],
            "other_activity": activity_tuple[4],
        }

    async def _get_all_activity(self, counted_channel_ids):
        # This database request includes 3 combined queries, they are described here below:
        #     1) The messages from MessageActivityLog        - other_activity is null
        #     2) Last on duty activity                       - other_activity is On duty activity
        #     3) When the bot started monitoring the officer - other_activity is Started monitoring
        result = await self.bot.officer_manager.send_db_request(
            """
            SELECT officer_id, channel_id, message_id, send_time, null AS "other_activity"
            FROM MessageActivityLog
            WHERE officer_id = %s
            UNION
            (SELECT officer_id, null, null, end_time, "On duty activity" AS "other_activity"
            FROM TimeLog
            WHERE officer_id = %s
                ORDER BY end_time DESC
                LIMIT 1)
            UNION
            (SELECT officer_id, null, null, started_monitoring_time, "Started monitoring" AS "other_activity"
            FROM Officers
            WHERE officer_id = %s)
            """,
            (self.id, self.id, self.id),
        )

        if result == None:
            return None
        # Filter all non-counted channels out
        return filter(lambda x: x[1] in counted_channel_ids or x[1] == None, result)
