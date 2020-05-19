# ====================
# Imports
# ====================

# Standard
import asyncio
import traceback

# Community
import aiomysql
import discord.errors as discord_errors
from pymysql import err as mysql_errors
import discord

# Mine
from Classes.Officer import Officer
from Classes.errors import MemberNotFoundError


class OfficerManager():

    def __init__(self, db, all_officer_ids, bot):
        self.bot = bot
        self.db = db

        # Get the guild
        self.guild = bot.get_guild(bot.settings["Server_ID"])
        if self.guild is None:
            print("ERROR Guild with ID",bot.settings["Server_ID"],"not found")
            print("Shutting down...")
            exit()

        # Get all monitored channels
        self.all_monitored_channels = [c.id for c in self.guild.channels if c.category not in bot.settings["monitored_channels"]["ignored_categories"] and isinstance(c, discord.channel.TextChannel)]

        # Add all the officers to the list
        self._all_officers = []
        print("Adding all the officers to the Officer Manager")
        for officer_id in all_officer_ids:
            try:
                new_officer = Officer(officer_id, bot)
                self._all_officers.append(new_officer)
                print(f"Added {new_officer.member.name}#{new_officer.member.discriminator} to the Officer Manager.")
            except MemberNotFoundError:
                print(f"The officer with the ID {officer_id} was not found in the server.")

        # Set up the automatically running code
        bot.loop.create_task(self.loop())

    @classmethod
    async def start(cls, bot, db_password):

        # Setup database
        db = await aiomysql.connect(
            host=bot.settings["DB_host"],
            port=3306,
            user=bot.settings["DB_user"],
            password=db_password,
            db=bot.settings["DB_name"],
            loop=asyncio.get_event_loop(),
            autocommit=True
        )
        
        # Fetch all the officers from the database
        try:
            cur = await db.cursor()
            await cur.execute("SELECT officer_id FROM Officers")
            result = await cur.fetchall()
            await cur.close()
        except Exception as error:
            print("ERROR failed to fetch officers from database:")
            print(error)
            print("Shutting down...")
            exit()
                
        return cls(db, (x[0] for x in result), bot)

    async def send_db_request(self, query, args):
        cur = await self.db.cursor()

        await cur.execute(query, args)
        result = await cur.fetchall()

        await cur.close()

        try: result[0][0]
        except IndexError: result = None

        return result


    # =====================
    #    Loop   
    # =====================

    async def loop(self):
        print("Running officer check loop in officer_manager")

        try:
            # Add missing officers
            for member in self.all_server_members_in_LPD:
                if not self.is_monitored(member.id):
                    await self.create_officer(member.id, issue="was not caught by on_member_update event")

            # Remove extra users from the officer_monitor
            for officer_member in self._all_officers:
                member_id = officer_member.id
                
                member = self.guild.get_member(member_id)

                if member is None:
                    await self.remove_officer(member_id, reason = "this person was not found in the server")
                    continue

                if self.is_officer(member) is False:
                    await self.remove_officer(member_id, reason="this person is in the server but does no longer have an LPD Officer role")
                    continue 

        except Exception as error:
            print(error)
            print(traceback.format_exc())

        await asyncio.sleep(self.bot.settings["sleep_time_between_officer_checks"])


    # =====================
    #    modify officers   
    # =====================
    
    def get_officer(self, officer_id):
        for officer in self._all_officers:
            if officer.id == officer_id:
                return officer
        return None

    async def create_officer(self, officer_id, issue=None):

        # Add the officer to the database
        try:
            cur = await self.db.cursor()
            await cur.execute("INSERT INTO Officers(officer_id) Values (%s)", (officer_id))
            await cur.close()
        except Exception as error:
            print("ERROR failed to add the officer with the ID",officer_id,"to the database:\n"+str(error))
            return None

        # Create the officer
        new_officer = Officer(officer_id, self.bot)

        # Add the officer to the _all_officers list
        self._all_officers.append(new_officer)

        # Print
        msg_string = "DEBUG: "+new_officer.display_name+" ("+str(new_officer.id)+") has been added to the LPD Officer Monitor"
        if issue is None: msg_string += " the correct way."
        else: msg_string += " but "+str(issue)
        print(msg_string)
        channel = self.bot.get_channel(self.bot.settings["error_log_channel"])
        await channel.send(msg_string)        

        # Return the officer
        return new_officer

    async def remove_officer(self, officer_id, reason=None):

        # Remove the officer from the database
        cur = await self.db.cursor()
        await cur.execute("DELETE FROM TimeLog WHERE officer_id = %s", (officer_id))
        await cur.execute("DELETE FROM Officers WHERE officer_id = %s", (officer_id))
        await cur.close()

        # Remove the officer from the officer list
        i = 0
        while i < len(self._all_officers):
            if self._all_officers[i].id == officer_id: del self._all_officers[i]
            else: i += 1

        msg_string = "WARNING: "+str(officer_id)+" has been removed from the LPD Officer Monitor"
        if reason is not None: msg_string += " because "+str(reason)
        print(msg_string)
        channel = self.bot.get_channel(self.bot.settings["error_log_channel"])
        await channel.send(msg_string)


    # ====================
    #    check officers   
    # ====================

    def is_officer(self, member):
        if member is None: return False
        all_lpd_ranks = [x["id"] for x in self.bot.settings["role_ladder"]]
        for role in member.roles:
            if role.id in all_lpd_ranks:
                return True
        return False

    def is_monitored(self, member_id):
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