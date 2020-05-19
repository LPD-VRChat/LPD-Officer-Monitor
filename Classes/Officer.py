# ====================
# Imports
# ====================

# Standard
import asyncio
import math
import time
from datetime import datetime

# Community
from discord import Member
from Classes.errors import MemberNotFoundError

# Mine
import Classes.extra_functions as ef


class Officer():
    def __init__(self, user_id, bot):
        self.bot = bot
        self.member = bot.get_guild(bot.settings["Server_ID"]).get_member(user_id)
        if self.member == None:
            raise MemberNotFoundError()

        self._on_duty_start_time = None
        self.is_on_duty = False

    def go_on_duty(self):

        print(self.discord_name+" is going on duty")

        # Print an error if the user is going on duty even though he is already on duty
        if self.is_on_duty is True:
            print("WARNING A user is going on duty even though he is already on duty")
            return
        
        # Start counting the officers time
        self._on_duty_start_time = time.time()
        self.is_on_duty = True
    
    async def go_off_duty(self):
        
        print(self.discord_name+" is going off duty")

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
        await self.bot.officer_manager.remove_officer(self)


    # ====================
    # properties
    # ====================

    # External functions
    
    @property
    def is_trainer(self):
        role_id = self.bot.officer_manager.bot.settings["trainer_role"]
        return self._has_role(role_id)
    
    @property
    def is_slrt_trainer(self):
        role_id = self.bot.officer_manager.bot.settings["slrt_trainer_role"]
        return self._has_role(role_id)
    
    @property
    def is_trained(self):
        cadet_id = self._get_settings_role("cadet")["id"]
        return not self._has_role(cadet_id)
    
    @property
    def is_slrt_trained(self):
        role_id = self.bot.officer_manager.bot.settings["slrt_trained_role"]
        return not self._has_role(role_id)
    

    # Often used member functions

    @property
    def discord_name(self):
        return self.member.name+"#"+self.member.discriminator

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

    def _get_settings_role(self, name_id):
        for role in self.bot.officer_manager.bot.settings["role_ladder"]:
            if role["name_id"] == name_id:
                return role
        raise ValueError("name_id not found in settings: "+str(name_id))

    def _has_role(self, role_id):
        for role in self.member.roles:
            if role.id == role_id:
                return True
        return False


    # ====================
    # On Duty Activity
    # ====================

    # External functions

    async def get_time_days(self, days=28):
        
        # Get the datetime objects
        from_datetime, to_datetime = await self._get_datetime_days(days)
        
        # Calclulate the time and return it
        return await self._get_time_datetime(from_datetime, to_datetime)

    async def get_time_date(self, from_date, to_date=None):

        # Get the datetime objects
        from_datetime, to_datetime = await self._get_datetime_date(from_date, to_date)

        # Calclulate the time and return it
        return await self._get_time_datetime(from_datetime, to_datetime)

    async def get_full_time_days(self, days=28):
        # Get the datetime objects
        from_datetime, to_datetime = await self._get_datetime_days(days)
        
        # Calclulate the time and return it
        return await self._get_full_time_datetime(from_datetime, to_datetime)

    async def get_full_time_date(self, from_date, to_date=None):
        # Get the datetime objects
        from_datetime, to_datetime = await self._get_datetime_date(from_date, to_date)

        # Calclulate the time and return it
        return await self._get_full_time_datetime(from_datetime, to_datetime)

    async def log_time(self, start_time, end_time):

        string_start_time = datetime.fromtimestamp(math.floor(start_time)).strftime(self.bot.officer_manager.bot.settings["db_time_format"])
        string_end_time = datetime.fromtimestamp(math.floor(end_time)).strftime(self.bot.officer_manager.bot.settings["db_time_format"])

        print("DEBUG Time logged for "+self.discord_name+": "+string_start_time+" - "+string_end_time+" Seconds: "+str(math.floor(end_time-start_time)))
        
        cur = await self.bot.officer_manager.db.cursor()
        args = (self.id, string_start_time, string_end_time)
        await cur.execute("INSERT INTO TimeLog(officer_id, start_time, end_time) VALUES (%s, %s, %s)", args)
        await cur.close()

    # Internal functions

    async def _get_datetime_days(self, days):

        # Create the datetime objects from the number of second since epoc
        from_datetime = datetime.fromtimestamp(math.floor(time.time() - days * 86400))
        to_datetime = datetime.fromtimestamp(math.floor(time.time()))

        # Return the datetime objects
        return (from_datetime, to_datetime)
    
    async def _get_datetime_date(self, from_date, to_date):

        from_date = from_date.split("/")
        try: to_date = to_date.split("/")
        except AttributeError: pass

        # Make sure the values are all their and are numbers
        for date in [from_date, to_date]:
            
            # This makes sure that the checks are 
            if date is None: continue

            # Make sure the length is correct
            if len(date) != 3:
                raise ValueError("Their is an error in the date you put in, make sure to split the date with a slash. Example: 30/2/2020")
            
            # Make sure all the things between the slashes are numbers
            for part in date:
                if not ef.is_number(part):
                    raise ValueError("The date you submitted does not only contain numbers, make sure that the date you submit only contains numbers and slashes. Example: 30/2/2020")

        # Translate the from_date into datetime a object
        from_datetime = datetime(int(from_date[2]), int(from_date[1]), int(from_date[0]), 0, 0)
        
        # If the to_date is none then it will set that as the current time
        if to_date is None: to_datetime = datetime.fromtimestamp(math.floor(time.time()))
        else: to_datetime = datetime(int(to_date[2]), int(to_date[1]), int(to_date[0]), 0, 0)

        # Return the datetime objects
        return (from_datetime, to_datetime)

    async def _get_time_datetime(self, from_datetime_object, to_datetime_object):
        # Convert the datetime objects into strings the database can understand
        from_db_time = from_datetime_object.strftime(self.bot.officer_manager.bot.settings["db_time_format"])
        to_db_time = to_datetime_object.strftime(self.bot.officer_manager.bot.settings["db_time_format"])

        # Execute the query to get the time information
        cur = await self.bot.officer_manager.db.cursor()
        query = """ SELECT SUM(end_time - start_time) AS 'Time'
                    FROM TimeLog
                    WHERE
                        officer_id = %s AND
                        (start_time > %s AND start_time < %s)"""
        args = (str(self.id), from_db_time, to_db_time)
        await cur.execute(query, args)
        result = await cur.fetchall()
        await cur.close()

        # Make sure the function will return a number even though the user has never gone on duty
        if result[0][0] is None: return 0
        else: return result[0][0]

    async def _get_full_time_datetime(self, from_datetime_object, to_datetime_object):
        # Convert the datetime objects into strings the database can understand
        from_db_time = from_datetime_object.strftime(self.bot.officer_manager.bot.settings["db_time_format"])
        to_db_time = to_datetime_object.strftime(self.bot.officer_manager.bot.settings["db_time_format"])

        # Execute the query to get the time information
        cur = await self.bot.officer_manager.db.cursor()
        query = """
        SELECT start_time, end_time, end_time - start_time AS 'duration'
        FROM TimeLog
        WHERE
            officer_id = %s AND
            (start_time > %s AND start_time < %s)"""
        # This is currently not in use
        """
        UNION
        SELECT null AS 'start_time', null AS 'end_time', SUM(end_time - start_time) AS 'duration'
        FROM TimeLog
        WHERE
            officer_id = %s AND
            (start_time > "%s" AND start_time < "%s")"""
        
        print("From datetime:",from_datetime_object)
        print("From:",from_db_time)
        print("To:",to_db_time)

        args = (str(self.id), from_db_time, to_db_time)
        await cur.execute(query, args)
        result = await cur.fetchall()
        await cur.close()

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
        if result == None: return None
        max_result = max(result, key=lambda x: time.mktime(x[3].timetuple()))

        return self._create_activity_dict(max_result)

    async def get_all_activity(self, counted_channel_ids):
        """
        This functions returns the last message times for an officer,
        the channels that are to be counted are passed into the function.
        """
        result = await self._get_all_activity(counted_channel_ids)

        if not result: return None
        return tuple(self._create_activity_dict(x) for x in result)

    async def log_message_activity(self, msg, send_time=None):
        
        # Set the send_time if it was not passed in, this was in
        # the kwargs but their it only ran once and gave the same
        # time every single time the function was run.
        if send_time == None:
            send_time = math.floor(time.time())
        
        # Make a string from the send_time the database can understand
        string_send_time = datetime.fromtimestamp(math.floor(send_time)).strftime(self.bot.officer_manager.bot.settings["db_time_format"])
        
        # Get the row ID for the last activity in the channel
        row_id = await self.bot.officer_manager.send_db_request(
            "SELECT entry_number FROM MessageActivityLog WHERE officer_id = %s AND channel_id = %s",
            (self.id, msg.channel.id)
        )

        # Insert the data into the database
        if row_id:
            row_id = row_id[0][0]
            await self.bot.officer_manager.send_db_request(
                "UPDATE MessageActivityLog SET message_id = %s, send_time = %s WHERE entry_number = %s",
                (msg.id, string_send_time, row_id)
            )
        else:
            await self.bot.officer_manager.send_db_request(
                "INSERT INTO MessageActivityLog(message_id, channel_id, officer_id, send_time) VALUES (%s, %s, %s, %s)",
                (msg.id, msg.channel.id, self.id, string_send_time)
            )

    # Internal functions

    def _create_activity_dict(self, activity_tuple):
        return {
            "officer_id": activity_tuple[0],
            "channel_id": activity_tuple[1],
            "message_id": activity_tuple[2],
            "time": activity_tuple[3]
        }

    async def _get_all_activity(self, counted_channel_ids):
        result = await self.bot.officer_manager.send_db_request(
            """
            SELECT officer_id, channel_id, message_id, send_time
            FROM MessageActivityLog
            WHERE officer_id = %s
            UNION
            (SELECT officer_id, 0, 0, end_time
            FROM TimeLog
            WHERE officer_id = %s
                ORDER BY end_time DESC
                LIMIT 1)
            """,
            (self.id, self.id)
        )
        
        if result == None: return None
        return filter(lambda x: x[1] in counted_channel_ids or x[1] == 0, result)