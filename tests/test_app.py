import pytest

from qbot.core import registry


@pytest.mark.asyncio
async def test_index(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.text == "☆ﾐ(o*･ω･)ﾉ Welcome to the future!"


@pytest.mark.asyncio
async def test_database_connection():
    assert await registry.database.execute("SELECT 1") == 1
