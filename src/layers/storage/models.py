import settings

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
import urllib.parse

import databases
import sqlalchemy
import ormar
import pydantic
from enum import Enum

if settings.CONFIG_LOADED == "base_test":
    import pytest

import discord
from discord.ext import commands

DATABASE_URL = f"{settings.DB_TYPE}://{settings.DB_USER}:{urllib.parse.quote(settings.DB_PASS)}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
if settings.CONFIG_LOADED == "base_test":
    DATABASE_URL = "sqlite+aiosqlite:///test.sqlite"

database = ormar.DatabaseConnection(DATABASE_URL)
_metadata = sqlalchemy.MetaData()
base_ormar_config = ormar.OrmarConfig(database=database, metadata=_metadata)


class User(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="users", abstract=True)

    id: int = ormar.BigInteger(primary_key=True)

    def member(self, bot) -> Optional[discord.Member]:
        """Return the discord.Member object with ID = self.id"""
        return bot.guild.get_member(self.id)


class BadgeCategory(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="badgecategory")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255)


class Badge(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="badges")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255)
    category: Optional[BadgeCategory] = ormar.ForeignKey(BadgeCategory)
    position: int = ormar.Integer(min_value=0)
    url: str = ormar.String(max_length=1024)


class Teams(Enum):
    val1 = "SLRT"


class CallTypes(Enum):
    val1 = "SLRT"
    val2 = "LMT"
    val3 = "Patrol"


class TrainingCategory(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="trainingcategories")

    id: int = ormar.Integer(primary_key=True)
    team: str = ormar.String(max_length=255, choices=list(Teams))
    name: str = ormar.String(max_length=255)


class Training(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="trainings")

    id: int = ormar.Integer(primary_key=True)
    category: Optional[TrainingCategory] = ormar.ForeignKey(TrainingCategory)
    name: str = ormar.String(max_length=255)


class OfficerBadgeOwned(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="officers_badges_owned")

    id: int = ormar.Integer(primary_key=True)


class OfficerBadgePrending(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="officers_badges_pending")

    id: int = ormar.Integer(primary_key=True)


class Officer(User):
    ormar_config = base_ormar_config.copy(tablename="officers")

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
    extra: pydantic.Json = ormar.JSON(default={})


class LOAEntry(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="loaentries")

    id: int = ormar.Integer(primary_key=True)
    officer: Optional[Officer] = ormar.ForeignKey(Officer)
    start: date = ormar.Date(timezone=True)
    end: date = ormar.Date(timezone=True)
    message_id: int = ormar.BigInteger(min_value=0, index=True)
    channel_id: int = ormar.BigInteger(min_value=0)
    created_at: datetime = ormar.DateTime(timezone=True)
    deleted_at: Optional[datetime] = ormar.DateTime(timezone=True, nullable=True)
    reason: str = ormar.String(max_length=4096)


class TimeRenewal(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="timerenewals")

    id: int = ormar.Integer(primary_key=True)
    officer: Optional[Officer] = ormar.ForeignKey(Officer, related_name="officer")
    timestamp: datetime = ormar.DateTime(timezone=True)
    renewer: Optional[Officer] = ormar.ForeignKey(Officer, related_name="renewer")


class StrikeEntry(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="strikeentries")

    id: int = ormar.Integer(primary_key=True)
    member_id: int = ormar.BigInteger(min_value=0, index=True)
    timestamp: datetime = ormar.DateTime(timezone=True)
    reason: str = ormar.String(max_length=4096)
    submitter: Optional[Officer] = ormar.ForeignKey(Officer)


class DetainedUser(User):
    ormar_config = base_ormar_config.copy(tablename="detainedusers")

    role_ids: pydantic.Json = ormar.JSON()


class Event(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="events")

    id: int = ormar.Integer(primary_key=True)
    start: datetime = ormar.DateTime(timezone=True)
    end: datetime = ormar.DateTime(timezone=True)
    hosts: pydantic.Json = ormar.JSON()


class SavedVoiceChannel(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="savedvoicechannels")

    id: int = ormar.BigInteger(primary_key=True)
    name: str = ormar.String(max_length=255)
    guild_id: int = ormar.BigInteger(min_value=0)

    def discord_channel(self, bot: commands.Bot) -> discord.VoiceChannel:
        return bot.get_channel(self.id)


class Patrol(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="patrols")

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
    ormar_config = base_ormar_config.copy(tablename="patrolvoices")

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
    ormar_config = base_ormar_config.copy(tablename="vrclocations")

    id: int = ormar.Integer(primary_key=True)
    instance_id: int = ormar.Integer(min_value=0)
    vrc_world_name: str = ormar.String(max_length=512)
    vrc_world_id: str = ormar.String(max_length=256)
    invite_token: str = ormar.String(max_length=256)
    instance_access_type: str = ormar.String(
        max_length=100, choices=list(VRCInstanceAccessTypeEnum)
    )
    start: datetime = ormar.DateTime(timezone=True)
    end: datetime = ormar.DateTime(timezone=True)
    patrol: Optional[Patrol] = ormar.ForeignKey(Patrol)


class Call(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="calls")

    id: int = ormar.Integer(primary_key=True)
    officers: Optional[List[Officer]] = ormar.ManyToMany(Officer)
    event: Optional[Event] = ormar.ForeignKey(Event)
    squad: Optional[SavedVoiceChannel] = ormar.ForeignKey(SavedVoiceChannel)
    type: str = ormar.String(max_length=10, choices=list(CallTypes))


class Payment(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="payments")

    id: int = ormar.Integer(primary_key=True)
    timestamp: datetime = ormar.DateTime()


class OfficerPayment(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="officerpayments")

    id: int = ormar.Integer(primary_key=True)
    amount: int = ormar.Integer()
    payment: Optional[Payment] = ormar.ForeignKey(Payment)
    officer: Optional[Officer] = ormar.ForeignKey(Officer)


@ormar.pre_relation_add([Officer])
async def officer_before_relation_add(
    sender, instance, child, relation_name, passed_kwargs, **kwargs
):
    # sender == Officer
    if type(child) == Badge:
        if child in instance.pending_badges:
            raise ormar.MultipleMatches
        if child in instance.badges:
            raise ormar.MultipleMatches
    elif type(child) == Training:
        if child in instance.trainings:
            raise ormar.MultipleMatches


if settings.CONFIG_LOADED == "base_test":

    @pytest.fixture(autouse=True, scope="module")
    def create_db():
        import os

        engine = sqlalchemy.create_engine(
            DATABASE_URL.replace("+aiosqlite", "+pysqlite")
        )  # DATABASE_URL)
        # _metadata.drop_all(engine)
        _metadata.create_all(engine)
        yield
        # _metadata.drop_all(engine)
        os.remove("test.sqlite")
