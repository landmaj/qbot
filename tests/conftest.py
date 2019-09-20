import pytest
from async_asgi_testclient import TestClient
from starlette.config import environ

from qbot.app import app
from qbot.core import registry


@pytest.fixture(autouse=True, scope="session")
def configuration():
    environ["TESTING"] = "True"
    registry.set_config_vars()


@pytest.fixture(autouse=True)
async def client():
    async with TestClient(app) as clnt:
        yield clnt
