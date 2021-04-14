# Event Manager - 02/16/2021 alpha testing

from discord.ext import tasks
from pytz import timezone
from pyteamup import Calendar, Event
from discord import Member
from datetime import datetime, timedelta


import asyncio
import nest_asyncio
nest_asyncio.apply()


class EventManager:
    def __init__(self, bot):
        self.bot = bot
        self.events = []
        self.bot.events = []

    @classmethod
    async def start(cls, bot, cal_id, api_key):
        instance = cls(bot)
        instance.cal_id = cal_id
        instance.api_key = api_key
        instance.update_cache.start()
        return instance

    @tasks.loop(hours=12)
    async def update_cache(self):

        # Get the TeamUp calendar and store the subcalendars for use elsewhere
        calendar = Calendar(self.cal_id, self.api_key)
        self.subcalendars = calendar.subcalendars

        # Set the search date range to UTCNOW +/-72h
        _start_date = datetime.utcnow() - timedelta(hours=72)
        _end_date = datetime.utcnow() + timedelta(hours=72)

        # Store all the event objects in cache
        self.all_events = calendar.get_event_collection(
            start_dt=_start_date, end_dt=_end_date)

        # Get all the existing event IDs with no attendees - we'll skip saving duplicates to avoid overwrites
        _existing_events = await self.bot.officer_manager.send_db_request("SELECT * FROM Events WHERE attendees IS NULL")
        _completed_events = await self.bot.officer_manager.send_db_request("SELECT event_id FROM Events WHERE attendees IS NOT NULL")
        existing_event_ids = []
        completed_event_ids = []
        for event in _existing_events:
            existing_event_ids.append(event[0])

        for event in _completed_events:
            completed_event_ids.append(event[0])

        for event in self.all_events:

            # If it doesn't have a host, or if it's already happened, skip it
            if event.who == "" or event.who == None or event.event_id in completed_event_ids:
                continue

            save = True

            # Format the times into a database-friendly format
            start_dt = event.start_dt.replace(
                tzinfo=timezone('UTC')).replace(tzinfo=None)
            end_dt = event.end_dt.replace(
                tzinfo=timezone('UTC')).replace(tzinfo=None)

            # Assume that event.who is the VRC name of the Host
            host_id = self.bot.user_manager.get_discord_by_vrc(event.who)

            # If we already have it, see if it's an exact match
            if event.event_id in existing_event_ids:
                for _event in _existing_events:
                    # If it's not the same event ID, it's not the one we're looking for
                    if _event[0] == event.event_id:
                        continue

                    # If this event exactly matches our saved/cached one, keep it
                    if _event[1] != host_id  or _event[2] != start_dt or _event[3] != end_dt:
                        await self.bot.officer_manager.send_db_request("DELETE FROM Events WHERE event_id = %s", (_event[0]))
                        await self.bot.officer_manager.send_db_request("REPLACE INTO Events (event_id, host_id, start_time, end_time) VALUES (%s, %s, %s, %s)", (event.event_id, host_id, start_dt, end_dt))
                    break

    async def log_attendance(self, event):

        # Get start and end times for searching stuff
        start_dt = event.start_dt.to_pydatetime().replace(
            tzinfo=timezone('UTC')).replace(tzinfo=None)
        end_dt = datetime.utcnow()
        latest_join_time = end_dt - timedelta(minutes=10)
        print(f"{end_dt} - {event.who} has stopped their event.")

        # Grab all recent on-duty officers that fall within the event window, and concatenate officer_ids into a CSV string
        attendee_ids = await self.bot.officer_manager.send_db_request("SELECT officer_id FROM TimeLog WHERE start_time > %s AND start_time < %s AND end_time < %s", (start_dt, latest_join_time, end_dt))
        attendees = ""
        for officer_id in attendee_ids:
            if len(attendees) == 0:
                attendees = f"{officer_id}"
                continue
            attendees = f"{attendees},{officer_id}"

        # Update the record we created earlier to add end_time and the attendee list
        await self.bot.officer_manager.send_db_request("UPDATE Events SET end_time = %s attendees = %s WHERE event_id = %s", (end_dt, attendees, event.event_id))

    async def get_event_by_id(self, event_id, update_cache=False):
        """
        Usage: self.bot.event_manager.get_event_by_id(event_id, update_cache=True)  - update cached events before getting the event
               self.bot.event_manager.get_event_by_id(event_id)                     - Get event from cache without updating (use this for repetitive calls)
        """

        if update_cache:
            await self.update_cache()

        for event in self.all_events:
            if event.event_id == event_id:
                return event

    async def get_events_by_datetime(self, start_dt, update_cache=False):
        """
        Usage: self.bot.event_manager.get_event_by_date(start_dt, update_cache=True)  - update cached events before getting the event
               self.bot.event_manager.get_event_by_date(start_dt)                     - Get event from cache without updating (use this for repetitive calls)
        """

        if update_cache:
            await self.update_cache()

        for event in self.all_events:
            if start_dt > event.start_dt.replace(tzinfo=timezone('UTC')).replace(tzinfo=None) and start_dt < event.end_dt.replace(tzinfo=timezone('UTC')).replace(tzinfo=None):
                return event
