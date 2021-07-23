import Settings
import Keys

from datetime import datetime
from typing import Optional, List, Dict

import databases
import sqlalchemy
import ormar
import pydantic
from enum import Enum

import discord
from discord.ext import commands

database = databases.Database(
    f"{Settings.DB_TYPE}://{Settings.DB_USER}:{Keys.DB_PASS}@{Settings.DB_HOST}:{Settings.DB_PORT}/{Settings.DB_NAME}"
)
metadata = sqlalchemy.MetaData()


class User(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)

    @property
    def member(self, bot) -> discord.Member:
        """Return the discord.Member object with ID = self.id"""
        return bot.guild.get_member(self.id)


class Officer(User):

    started_monitoring: datetime = ormar.DateTime(timezone=True)
    vrchat_name: str = ormar.String(max_length=255)
    vrchat_id: str = ormar.String(max_length=255)
    badges: Optional[List[Badge]] = ormar.ManyToMany(Badge)
    pending_badges: Optional[List[Badge]] = ormar.ManyToMany(Badge)
    trainings: Optional[List[Training]] = ormar.ManyToMany(Training)


class BadgeCategory(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255)


class Badge(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255)
    category: BadgeCategory = ormar.ManyToOne(BadgeCategory)
    position: int = ormar.Integer(min_value=0)
    url: str = ormar.String(max_length=65536)


class Teams(Enum):
    val1 = "SLRT"


class CallTypes(Enum):
    val1 = "SLRT"
    val2 = "LMT"
    val3 = "Patrol"


class TrainingCategory(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    team: str = ormar.String(max_length=255, choices=list(Team))
    name: str = ormar.String(max_length=255)


class Training(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    category: TrainingCategory = ormar.ManyToOne(TrainingCategory)
    name: str = ormar.String(max_length=255)


class LOAEntry(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    officer_id: int = ormar.Integer(primary_key=True)
    start: date = ormar.Date(timezone=True)
    end: date = ormar.Date(timezone=True)
    message_id: int = ormar.Integer(min_value=0)
    channel_id: int = ormar.Integer(min_value=0)


class TimeRenewal(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    officer_id: int = ormar.Integer(primary_key=True)
    timestamp: datetime = ormar.DateTime(timezone=True)
    renewer: Officer


class StrikeEntry(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    member_id: int = ormar.Integer(min_value=0)
    timestamp: datetime = ormar.DateTime(timezone=True)
    reason: str = ormar.String(max_length=65536)
    submitter: Officer


class DetainedUser(User):
    role_ids: pydantic.Json = ormar.Json()


class Event(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    start: datetime = ormar.DateTime(timezone=True)
    end: datetime = ormar.DateTime(timezone=True)
    hosts: pydantic.Json = ormar.Json()


class SavedVoiceChannel(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255)
    guild_id: int = ormar.Integer(min_value=0)

    def discord_channel(bot: commands.Bot) -> discord.VoiceChannel:
        return bot.get_channel(self.id)


class Patrol(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    officer_id: int = ormar.Integer(min_value=0)
    start: datetime = ormar.DateTime(timezone=True)
    end: datetime = ormar.DateTime(timezone=True)
    event_id: Optional[int] = ormar.Integer(min_value=0)
    main_channel: SavedVoiceChannel


class PatrolVoice(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    patrol_id: int = ormar.Integer(primary_key=True)
    channel: SavedVoiceChannel
    start: datetime = ormar.DateTime(timezone=True)
    end: datetime = ormar.DateTime(timezone=True)


class VRCLocation(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    instance_id: int = ormar.Integer(min_value=0)
    vrc_world_name: str = ormar.String(max_length=65536)
    vrc_world_id: str = ormar.String(max_length=65536)
    invite_token: str = ormar.String(max_length=65536)
    instance_access_type: str = Enum(["Public", "Private", "Secret"])
    start: datetime = ormar.DateTime(timezone=True)
    end: datetime = ormar.DateTime(timezone=True)
    patrol_id: int = ormar.Integer(min_value=0)


class Call(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    officers: Optional[List[Officer]] = ormar.ManyToMany(Officer)
    event: Optional[Event] = ormar.ManyToOne(Event)
    squad: SavedVoiceChannel
    type: str = ormar.String(max_length=10, choices=list(CallTypes))
