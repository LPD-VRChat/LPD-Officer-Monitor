# ====================
# Imports
# ====================

# Standard
import asyncio
import traceback

# Community
import aiomysql

# Mine
from .Officer import Officer


class OfficerManager():

    def __init__(self, db, all_officers, guild, bot):
        self.db = db
        self._all_officers = all_officers
        self.guild = guild
        self.bot = bot

    @classmethod
    async def start(cls, bot, db_password):
        
        # Get the guild
        guild = bot.get_guild(bot.settings["Server_ID"])
        if guild is None:
            print("ERROR Guild with ID",bot.settings["Server_ID"],"not found")
            print("Shutting down...")
            exit()

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

        # Initialize the officer_manager instance so that it can be added with each created officer
        print("Initializing instance of Officer Manager")
        instance = cls(db, [], guild, bot)

        # Add all the officers to this instance
        print("Adding all the officers to the Officer Manager")
        for officer in result:
            new_officer = await Officer.create(officer[0], instance)
            instance._all_officers.append(new_officer)
            print("Added "+new_officer.name+"#"+new_officer.discriminator,"to the Officer Manager")
        
        # Set up the automatically running code
        bot.loop.create_task(instance.loop())

        # Return the instance
        print("Officer Manager ready")
        return instance


    # =====================
    #    Loop   
    # =====================

    async def loop(self):
        print("Running officer check loop in officer_manager")

        try:
            # Add missing officers
            for member in self.all_server_members_in_LPD:
                if not self.is_monitored(member.id):
                    await self.create_officer(member.id)
                    await self.bot.get_channel(self.bot.settings["error_log_channel"]).send("WARNING: "+member.mention+" ("+str(member.id)+") has been added to the LPD Officer Monitor without being caught by on_member_update event")

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
        new_officer = await Officer.create(officer_id, self)

        # Add the officer to the _all_officers list
        self._all_officers.append(new_officer)

        # Print
        msg_string = "DEBUG: "+new_officer.mention+" ("+str(new_officer.id)+") has been added to the LPD Officer Monitor"
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
