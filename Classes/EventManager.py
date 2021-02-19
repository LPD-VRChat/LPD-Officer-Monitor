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

    """
    async def stop(self):

        self.
    """

    @classmethod
    async def start(cls, bot, cal_id, api_key):
        instance = cls(bot)
        instance.cal_id = cal_id
        instance.api_key = api_key
        instance.main.start()
        return instance

    async def update_cache(self):
        calendar = Calendar(self.cal_id, self.api_key)
        self.subcalendars = calendar.subcalendars

        _start_date = datetime.utcnow() - timedelta(hours=6)
        _end_date = datetime.utcnow() + timedelta(hours=30)

        self.all_events = calendar.get_event_collection(
            start_date=_start_date, end_date=_end_date)

        existing_event_ids = await self.bot.officer_manager.send_db_request("SELECT event_id FROM Events")

        for event in self.all_events:
            if event.event_id in existing_event_ids:
                continue

            if event.who == "" or event.who == None:
                continue

            start_dt = event.start_dt.replace(
                tzinfo=timezone('UTC')).replace(tzinfo=None)
            end_dt = event.end_dt.replace(
                tzinfo=timezone('UTC')).replace(tzinfo=None)

            host_id = self.bot.user_manager.get_discord_by_vrc(event.who)

            await self.bot.officer_manager.send_db_request("INSERT INTO Events (event_id, host_id, start_time, end_time) VALUES (%s, %s, %s)", event.event_id, host_id, start_dt, end_dt)

    @tasks.loop(hours=12)
    async def main(self):
        await self.update_cache()

    async def log_attendance(self, event):
        start_dt = event.start_dt.replace(
            tzinfo=timezone('UTC')).replace(tzinfo=None)
        end_dt = datetime.utcnow()
        latest_join_time = end_dt - timedelta(minutes=10)
        print(f"{end_dt} - {event.who} has stopped their event.")

        # Grab all recent on-duty officers that fall within the event window, and concatenate officer_ids into a CSV string
        attendee_ids = await self.bot.officer_manager.send_db_request("SELECT officer_id FROM TimeLog WHERE start_time > %s AND start_time < %s AND end_time < %s", start_dt, latest_join_time, end_dt)
        attendees = ""
        for officer_id in attendee_ids:
            if len(attendees) == 0:
                attendees = f"{officer_id}"
                continue
            attendees = f"{attendees},{officer_id}"

        # Update the record we created earlier to add end_time and the attendee list
        await self.bot.officer_manager.send_db_request("UPDATE Events SET end_time = %s attendees = %s WHERE event_id = %s", end_dt, attendees, event.event_id)

    async def render_events(self):
        parsed_events = []

        for event in self.all_events:
            event_time = event.start_dt.replace(
                tzinfo=timezone('UTC')).replace(tzinfo=None)

            for cal in self.subcalendars:
                if cal['id'] in event.subcalendar_ids:
                    event_cal = cal['name']
                    break
                else:
                    event_cal = None

            if event.who == None or event.who == "":
                who = ""
            else:
                who = event.who

            tmp_dict = {"title": event.title,
                        "time": str(event_time),
                        "host": who,
                        "calendar": event_cal}

            parsed_events.append(tmp_dict)

        self.events = parsed_events
        self.bot.events = parsed_events

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
