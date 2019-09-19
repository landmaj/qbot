import pytest
from async_asgi_testclient import TestClient
from sqlalchemy import create_engine
from starlette.config import environ

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
async def client():
    async with TestClient(app) as clnt:
        yield clnt
