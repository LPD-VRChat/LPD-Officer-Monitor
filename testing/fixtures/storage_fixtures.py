from _pytest import config
import src.layers.storage.models
import pytest
import settings
import sqlalchemy
import databases
import os
import logging
import pytest_asyncio
import testing.fixtures.default_data_fixtures

URL = "sqlite+aiosqlite:///test.sqlite"


# @pytest.fixture(scope="module")
@pytest_asyncio.fixture(scope="module")
async def create_db():
    assert settings.CONFIG_LOADED == "base_test"
    try:
        os.remove("test.sqlite")
    except FileNotFoundError:
        pass
    except PermissionError:
        pass #probably a bad idea to suppress this
    #assert URL == src.layers.storage.models.DATABASE_URL
    engine = sqlalchemy.create_engine(URL.replace('+aiosqlite', '+pysqlite'))  # DATABASE_URL)
    logging.info("Creating database")

    # src.layers.storage.models.metadata = sqlalchemy.MetaData()
    src.layers.storage.models._metadata.drop_all(engine)
    src.layers.storage.models._metadata.create_all(engine)
    await src.layers.storage.models.database.connect()
    # await src.layers.storage.models.database.execute("PRAGMA foreign_keys=ON")
    yield
    # database.metadata.drop_all(engine)
    # os.remove("test.sqlite")


@pytest_asyncio.fixture
async def reset_database():
    """Fixture to reset database to known state for specific tests"""
    await testing.fixtures.default_data_fixtures.destroy_db()
    await testing.fixtures.default_data_fixtures.setup_db_data()
    yield
    # Optional: cleanup after test if needed
