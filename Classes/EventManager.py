# Event Manager - 02/16/2021 alpha testing

from discord.ext import tasks
from pytz import timezone
from pyteamup import Calendar, Event
from discord import Member
from datetime import datetime, timedelta
import json
import asyncio
import nest_asyncio
nest_asyncio.apply()


class EventManager:
    def __init__(self, bot):
        self.bot = bot
        self.events = []
        self.bot.events = []

    """async def start(self, host):

        print(f"{self.start_time} - {self.host.displayName} has started an event scheduled to end {self.end_time}.")

        await self.bot.officer_manager.send_db_request("INSERT INTO Events (host_id, start_time, end_time) VALUES (%s, %s, %s)", host.id, self.start_time, self.end_time)

    async def stop(self):

        self.end_time = datetime.utcnow()
        latest_join_time = self.end_time - timedelta(minutes=10)
        print(f"{self.end_time} - {self.host.displayName} has stopped their event.")

        # Grab all recent on-duty officers that fall within the event window, and concatenate officer_ids into a CSV string
        attendee_ids = await self.bot.officer_manager.send_db_request("SELECT officer_id FROM TimeLog WHERE start_time > %s AND start_time < %s AND end_time < %s", self.start_time, latest_join_time, self.end_time)
        attendees = ""
        for officer_id in attendee_ids:
            if len(attendees) == 0:
                attendees = f"{officer_id}"
                continue
            attendees = f"{attendees},{officer_id}"

        # Update the record we created earlier to add end_time and the attendee list
        await self.bot.officer_manager.send_db_request("UPDATE Events SET end_time = %s attendees = %s WHERE start_time = (SELECT MAX(start_time) FROM Events WHERE host_id = %s", self.end_time, attendees, self.host.id)
    """

    @classmethod
    async def start(cls, bot, cal_id, api_key):
        instance = cls(bot)
        instance.cal_id = cal_id
        instance.api_key = api_key
        instance.main.start()
        return instance

    def update(self):
        calendar = Calendar(self.cal_id, self.api_key)

        _start_date = datetime.utcnow() - timedelta(hours=6)
        _end_date = datetime.utcnow() + timedelta(hours=30)

        all_events = calendar.get_event_collection(
            start_date=_start_date, end_date=_end_date)
        parsed_events = []

        # print(all_events)
        for event in all_events:
            event_time = event.start_dt.replace(
                tzinfo=timezone('UTC')).replace(tzinfo=None)
            if event_time < datetime.utcnow():
                continue
            if event_time > datetime.utcnow() + timedelta(days=7):
                continue

            for cal in calendar.subcalendars:
                if cal['id'] in event.subcalendar_ids:
                    event_cal = cal
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
                        "calendar": event_cal['name']}

            #print(event.title, str(event_time)+' UTC')
            parsed_events.append(tmp_dict)

        # print(parsed_events)
        self.events = parsed_events
        self.bot.events = parsed_events

        #output = json.dumps(self.events, indent=4)
        # print(output)

    @tasks.loop(hours=12)
    async def main(self):
        self.update()
