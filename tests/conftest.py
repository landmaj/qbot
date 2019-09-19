import pytest
from sqlalchemy import create_engine
from starlette.config import environ
from starlette.testclient import TestClient

from qbot.app import app
from qbot.core import registry
from qbot.db import metadata


@pytest.fixture(autouse=True, scope="session")
def configuration():
    environ["TESTING"] = "True"
    registry.set_config_vars()


@pytest.fixture(autouse=True, scope="session")
def create_tables(configuration):
    engine = create_engine(str(registry.DATABASE_URL))
    metadata.create_all(engine)


@pytest.fixture(autouse=True)
async def setup_registry():
    await registry.setup()
    yield registry
    await registry.teardown()


@pytest.fixture()
def client():
    return TestClient(app)
