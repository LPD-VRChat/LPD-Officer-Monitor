import asyncio
import aiomysql
from .Officer import Officer

class OfficerManager():

    def __init__(self, db, all_officers, guild):
        self.db = db
        self._all_officers = all_officers
        self.guild = guild

    @classmethod
    async def start(cls, client, server_id, db_name, db_user, db_host, db_password):
        
        # Get the guild
        guild = client.get_guild(server_id)
        if guild is None:
            print("ERROR Guild with ID",server_id,"not found")
            print("Shutting down...")
            exit()

        # Setup database
        db = await aiomysql.connect(
            host=db_host,
            port=3306,
            user=db_user,
            password=db_password,
            db=db_name,
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
        instance = cls(db, [], guild)

        # Add all the officers to this instance
        print("Adding all the officers to the Officer Manager")
        for officer in result:
            new_officer = await Officer.create(officer[0], guild, instance)
            instance._all_officers.append(new_officer)
            print("Added "+new_officer.name+"#"+new_officer.discriminator,"to the Officer Manager")
        
        # Return the instance
        print("Officer Manager ready")
        return instance

    def get_officer(self, officer_id):
        officer_iterator = filter(lambda x: x.id == officer_id, self._all_officers)
        return next(officer_iterator)

    async def create_officer(self, officer_id):

        # Add the officer to the database
        try:
            cur = await self.db.cursor()
            await cur.execute("INSERT INTO Officers(officer_id) Values (%s)", (officer_id))
            await cur.close()
        except Exception as error:
            print("ERROR failed to add the officer with the ID",officer_id,"to the database:\n"+str(error))
            return None

        # Create the officer
        new_officer = await Officer.create(officer_id, self.guild, self)

        # Add the officer to the _all_officers list
        self._all_officers.append(new_officer)

        # Print
        print(new_officer.discord_name+" has been added to the officer_manager")

        # Return the officer
        return new_officer

    def is_officer(self, member):
        return member.id in self._all_officers

    async def remove_officer(self, officer):

        # Remove the officer from the database
        cur = await self.db.cursor()
        await cur.execute("DELETE FROM Officers WHERE officer_id = %s", (officer.id))
        await cur.close()
        
        # Remove the officer from the officer list
        self._all_officers.remove(officer)

        # Print
        print(officer.discord_name+" has been removed from the officer_manager")

        # Remove the officer instance
        del officer

    @property
    def all_officers(self):
        return self._all_officers