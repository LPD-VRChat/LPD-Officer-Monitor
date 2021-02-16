# Event Manager - 02/16/2021 alpha testing

import asyncio
import json

from datetime import datetime, timedelta
from discord import Member
from pyteamup import Calendar, Event
from pytz import timezone


class EventManager:
    def __init__(self, bot, host):
        self.bot = bot
        self.start_time = datetime.utcnow()
        self.end_time = datetime.utcnow() + timedelta(hours=2)
        self.host = host

    async def start(self, host):

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

    def get_calendar_events(cal_id, api_key):
        calendar = Calendar(cal_id, api_key)
        all_events = calendar.get_event_collection()
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
                if cal['id'] == event.subcalendar_ids:
                    event_cal = cal
                    break
                else:
                    event_cal = None

            tmp_dict = {"title": event.title,
                        "time": event_time,
                        "host": event.who,
                        "calendar": event_cal['name']}

            #print(event.title, str(event_time)+' UTC')
            parsed_events.append(tmp_dict)

        # print(parsed_events)
        output = json.dumps(json.loads(parsed_events), indent=4)
        print(output)
