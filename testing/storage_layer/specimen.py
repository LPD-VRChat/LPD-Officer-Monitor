from sqlite3 import IntegrityError
import sys
import os

sys.path.append(os.getcwd())
import src.layers.storage.models as models

import datetime
import logging
import pymysql
import ormar


async def create_or_get_exemple_user(name: str, id: int):
    officer = await models.Officer.objects.create(
        id=id,
        started_monitoring=datetime.datetime.now(),
        vrchat_name=name,
        vrchat_id="usr_ffffffff-ffff-ffff-fffffff",
        deleted_at=None,
    )
    return officer


async def create_exemple_trainings():
    tcat = await models.TrainingCategory.objects.create(
        team=models.Teams.val1.value, name="medical bonk"
    )
    await models.Training.objects.create(category=tcat, name="bonk101")
    await models.Training.objects.create(category=tcat, name="bonk202")


async def create_exemple_badges():
    cat = await models.BadgeCategory.objects.create(name="Category Name")
    await models.Badge.objects.create(name="badge1", category=cat, position=0, url="")
    await models.Badge.objects.create(name="badge2", category=cat, position=0, url="")


async def create_exemple_data():
    try:
        officer1 = await create_or_get_exemple_user("xXxHeisenbergxXx", 1)
        officer2 = await create_or_get_exemple_user("Username420", 2)
        await create_exemple_trainings()
        await create_exemple_badges()
    except pymysql.err.IntegrityError:  ## data already created
        officer1 = await models.Officer.objects.get(id=1)
        officer2 = await models.Officer.objects.get(id=2)

    badge = await models.Badge.objects.get()  # last

    ##this create duplicated ManyToMany entries
    await officer1.pending_badges.add(badge)
    await officer1.update()

    await officer2.badges.add(badge)
    await officer2.update()

    await badge.load_all()
    await officer1.load_all()

    try:
        await officer1.pending_badges.add(badge)
    except ormar.MultipleMatches:
        print("duplicate detected")

    print(
        await badge.current_badges.all()
    )  ##also gets officer, may need .fetch() if there is missing attributes


async def main():
    logging.debug("starting")
    if not models.database.is_connected:
        await models.database.connect()
    # for table in reversed(models.metadata.sorted_tables):
    #     await models.database.execute(f"TRUNCATE TABLE {table.name}")
    #     # await con.execute(table.delete())
    import sqlalchemy

    engine = sqlalchemy.create_engine(models.DATABASE_URL)
    models.metadata.drop_all(engine)
    models.metadata.create_all(engine)
    logging.debug("exemple_data")
    await create_exemple_data()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
