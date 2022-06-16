import settings

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
import urllib.parse

import databases
import sqlalchemy
import ormar
import pydantic
import pytest
from enum import Enum

import discord
from discord.ext import commands

DATABASE_URL = f"{settings.DB_TYPE}://{settings.DB_USER}:{urllib.parse.quote(settings.DB_PASS)}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
database = databases.Database(DATABASE_URL)
database.url = databases.DatabaseURL(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class User(ormar.Model):
    class Meta(BaseMeta):
        # tablename = "users"
        abstract = True

    id: int = ormar.BigInteger(primary_key=True)

    def member(self, bot) -> Optional[discord.Member]:
        """Return the discord.Member object with ID = self.id"""
        return bot.guild.get_member(self.id)


class BadgeCategory(ormar.Model):
    class Meta(BaseMeta):
        tablename = "badgecategory"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255)


class Badge(ormar.Model):
    class Meta(BaseMeta):
        tablename = "badges"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255)
    category: Optional[BadgeCategory] = ormar.ForeignKey(BadgeCategory)
    position: int = ormar.Integer(min_value=0)
    url: str = ormar.Text()


class Teams(Enum):
    val1 = "SLRT"


class CallTypes(Enum):
    val1 = "SLRT"
    val2 = "LMT"
    val3 = "Patrol"


class TrainingCategory(ormar.Model):
    class Meta(BaseMeta):
        tablename = "trainingcategories"

    id: int = ormar.Integer(primary_key=True)
    team: str = ormar.String(max_length=255, choices=list(Teams))
    name: str = ormar.String(max_length=255)


class Training(ormar.Model):
    class Meta(BaseMeta):
        tablename = "trainings"

    id: int = ormar.Integer(primary_key=True)
    category: Optional[TrainingCategory] = ormar.ForeignKey(TrainingCategory)
    name: str = ormar.String(max_length=255)


class OfficerBadgeOwned(ormar.Model):
    class Meta(BaseMeta):
        tablename = "officers_badges_owned"

    id: int = ormar.Integer(primary_key=True)


class OfficerBadgePrending(ormar.Model):
    class Meta(BaseMeta):
        tablename = "officers_badges_pending"

    id: int = ormar.Integer(primary_key=True)


class Officer(User):
    class Meta(BaseMeta):
        tablename = "officers"

    started_monitoring: datetime = ormar.DateTime(timezone=True)
    # TODO: Index this column
    deleted_at: Optional[datetime] = ormar.DateTime(timezone=True, nullable=True)
    vrchat_name: str = ormar.String(max_length=255)
    vrchat_id: str = ormar.String(max_length=255)
    badges: Optional[List[Badge]] = ormar.ManyToMany(
        Badge,
        related_name="current_badges",
        through=OfficerBadgeOwned,
        through_relation_name="officer_id_owned",
        through_reverse_relation_name="badge_id_owned",
    )  ##TODO : check if relation actually works both ways
    pending_badges: Optional[List[Badge]] = ormar.ManyToMany(
        Badge,
        related_name="pending_badges",
        through=OfficerBadgePrending,
        through_relation_name="officer_id_pending",
        through_reverse_relation_name="badge_id_pending",
    )
    trainings: Optional[List[Training]] = ormar.ManyToMany(Training)


class LOAEntry(ormar.Model):
    class Meta(BaseMeta):
        tablename = "loaentries"

    id: int = ormar.Integer(primary_key=True)
    officer: Optional[Officer] = ormar.ForeignKey(Officer)
    start: date = ormar.Date(timezone=True)
    end: date = ormar.Date(timezone=True)
    message_id: int = ormar.BigInteger(min_value=0)
    channel_id: int = ormar.BigInteger(min_value=0)


class TimeRenewal(ormar.Model):
    class Meta(BaseMeta):
        tablename = "timerenewals"

    id: int = ormar.Integer(primary_key=True)
    officer: Optional[Officer] = ormar.ForeignKey(Officer, related_name="officer")
    timestamp: datetime = ormar.DateTime(timezone=True)
    renewer: Optional[Officer] = ormar.ForeignKey(Officer, related_name="renewer")


class StrikeEntry(ormar.Model):
    class Meta(BaseMeta):
        tablename = "strikeentries"

    id: int = ormar.Integer(primary_key=True)
    member_id: int = ormar.BigInteger(min_value=0)
    timestamp: datetime = ormar.DateTime(timezone=True)
    reason: str = ormar.Text()
    submitter: Optional[Officer] = ormar.ForeignKey(Officer)


class DetainedUser(User):
    class Meta(BaseMeta):
        tablename = "detainedusers"

    role_ids: pydantic.Json = ormar.JSON()


class Event(ormar.Model):
    class Meta(BaseMeta):
        tablename = "events"

    id: int = ormar.Integer(primary_key=True)
    start: datetime = ormar.DateTime(timezone=True)
    end: datetime = ormar.DateTime(timezone=True)
    hosts: pydantic.Json = ormar.JSON()


class SavedVoiceChannel(ormar.Model):
    class Meta(BaseMeta):
        tablename = "savedvoicechannels"

    id: int = ormar.BigInteger(primary_key=True)
    name: str = ormar.String(max_length=255)
    guild_id: int = ormar.BigInteger(min_value=0)

    def discord_channel(self, bot: commands.Bot) -> discord.VoiceChannel:
        return bot.get_channel(self.id)


class Patrol(ormar.Model):
    class Meta(BaseMeta):
        tablename = "patrols"

    id: int = ormar.Integer(primary_key=True)
    officer: Optional[Officer] = ormar.ForeignKey(Officer)
    start: datetime = ormar.DateTime(timezone=True)
    end: datetime = ormar.DateTime(timezone=True)
    event: Optional[Event] = ormar.ForeignKey(Event, nullable=True)
    main_channel: Optional[SavedVoiceChannel] = ormar.ForeignKey(SavedVoiceChannel)

    def duration(self) -> timedelta:
        return self.end - self.start

    def __hash__(self) -> int:
        # Make sure we don't have the same hash as the ids only, could wreck havoc
        # in an non typed dictionary.
        return hash((10633291031406973, self.id))


class PatrolVoice(ormar.Model):
    class Meta(BaseMeta):
        tablename = "patrolvoices"

    id: int = ormar.Integer(primary_key=True)
    patrol: Optional[Patrol] = ormar.ForeignKey(Patrol)
    channel: Optional[SavedVoiceChannel] = ormar.ForeignKey(SavedVoiceChannel)
    start: datetime = ormar.DateTime(timezone=True)
    end: datetime = ormar.DateTime(timezone=True)

    def duration(self) -> timedelta:
        return self.end - self.start


class VRCInstanceAccessTypeEnum(Enum):
    val1 = "Public"
    val2 = "Private"
    val3 = "Secret"


class VRCLocation(ormar.Model):
    class Meta(BaseMeta):
        tablename = "vrclocations"

    id: int = ormar.Integer(primary_key=True)
    instance_id: int = ormar.Integer(min_value=0)
    vrc_world_name: str = ormar.Text()
    vrc_world_id: str = ormar.Text()
    invite_token: str = ormar.Text()
    instance_access_type: str = ormar.String(
        max_length=100, choices=list(VRCInstanceAccessTypeEnum)
    )
    start: datetime = ormar.DateTime(timezone=True)
    end: datetime = ormar.DateTime(timezone=True)
    patrol: Optional[Patrol] = ormar.ForeignKey(Patrol)


class Call(ormar.Model):
    class Meta(BaseMeta):
        tablename = "calls"

    id: int = ormar.Integer(primary_key=True)
    officers: Optional[List[Officer]] = ormar.ManyToMany(Officer)
    event: Optional[Event] = ormar.ForeignKey(Event)
    squad: Optional[SavedVoiceChannel] = ormar.ForeignKey(SavedVoiceChannel)
    type: str = ormar.String(max_length=10, choices=list(CallTypes))


@pytest.fixture(autouse=True, scope="module")
def create_db():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)
