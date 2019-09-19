import pytest

from qbot.core import registry


@pytest.mark.asyncio
async def test_index(client):
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ping(client):
    response = await client.get("/ping")
    assert response.status_code == 200
    assert response.text == "pong"


@pytest.mark.asyncio
async def test_database_connection():
    assert await registry.database.execute("SELECT 1") == 1
