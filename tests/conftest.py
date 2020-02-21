import pytest
from async_asgi_testclient import TestClient

from qbot.app import app
from qbot.core import registry


@pytest.fixture(autouse=True, scope="session")
def configuration():
    registry.set_config_vars()


@pytest.fixture(autouse=True)
async def client():
    async with TestClient(app) as clnt:
        yield clnt
