from unittest.mock import ANY, patch

import pytest
from asynctest import CoroutineMock

from qbot.core import registry
from qbot.db import fortunki
from qbot.utils import get_recently_seen
from tests.utils import send_slack_request


@pytest.mark.asyncio
async def test_add_recently_seen_when_cache_does_not_exist(client):
    event = {
        "event": {
            "type": "message",
            "channel": "C2147483705",
            "user": "U2147483697",
            "text": "!fortunka",
            "ts": "1355517523.000005",
        },
        "event_id": "Ev9UQ52YNA",
    }
    values = [{"text": "1"}, {"text": "2"}, {"text": "3"}, {"text": "4"}]
    await registry.database.execute_many(
        query=f"INSERT INTO {fortunki.fullname}(text) VALUES (:text)", values=values
    )
    if hasattr(fortunki, "cache"):
        delattr(fortunki, "cache")
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        mock.assert_called_once_with(ANY, text=ANY)
    assert response.status_code == 200
    assert response.text == "OK"
    assert type(fortunki.cache) == set
    assert len(fortunki.cache) == 1


@pytest.mark.asyncio
async def test_add_recently_seen_when_cache_exists(client):
    event = {
        "event": {
            "type": "message",
            "channel": "C2147483705",
            "user": "U2147483697",
            "text": "!fortunka",
            "ts": "1355517523.000005",
        },
        "event_id": "Ev9UQ52YNA",
    }
    values = [{"text": "1"}, {"text": "2"}, {"text": "3"}, {"text": "4"}]
    await registry.database.execute_many(
        query=f"INSERT INTO {fortunki.fullname}(text) VALUES (:text)", values=values
    )
    fortunki.cache = set()
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        mock.assert_called_once_with(ANY, text=ANY)
    assert response.status_code == 200
    assert response.text == "OK"
    assert type(fortunki.cache) == set
    assert len(fortunki.cache) == 1


@pytest.mark.asyncio
async def test_get_recently_seen(client):
    event = {
        "event": {
            "type": "message",
            "channel": "C2147483705",
            "user": "U2147483697",
            "text": "!fortunka",
            "ts": "1355517523.000005",
        },
        "event_id": "Ev9UQ52YNA",
    }
    values = [{"text": "1"}, {"text": "2"}]
    await registry.database.execute_many(
        query=f"INSERT INTO {fortunki.fullname}(text) VALUES (:text)", values=values
    )
    if hasattr(fortunki, "cache"):
        delattr(fortunki, "cache")
    if hasattr(fortunki, "cache_max_size"):
        delattr(fortunki, "cache_max_size")
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        for _ in range(10):
            await send_slack_request(event, client)
            await send_slack_request(event, client)
            first_call = mock.call_args_list[0]
            second_call = mock.call_args_list[1]
            assert (
                first_call[1]["text"] != second_call[1]["text"] != "Nie ma fortunek :("
            )
    assert type(fortunki.cache) == set
    assert len(fortunki.cache) == 1


@pytest.mark.parametrize(
    ["number_of_inputs", "expected_cache_size", "number_of_requests"],
    [
        (0, 0, 1),
        (0, 0, 2),
        (1, 0, 1),
        (1, 0, 2),
        (2, 0, 1),
        (2, 0, 2),
        (3, 0, 1),
        (3, 0, 2),
        (4, 1, 1),
        (4, 0, 2),
        (4, 1, 3),
        (6, 1, 1),
        (6, 2, 2),
        (6, 0, 3),
    ],
)
@pytest.mark.asyncio
async def test_get_recently_seen_cache_size(
    client, number_of_inputs, expected_cache_size, number_of_requests
):
    event = {
        "event": {
            "type": "message",
            "channel": "C2147483705",
            "user": "U2147483697",
            "text": "!fortunka",
            "ts": "1355517523.000005",
        },
        "event_id": "Ev9UQ52YNA",
    }
    values = []
    for x in range(number_of_inputs):
        values.append({"text": str(x)})
    await registry.database.execute_many(
        query=f"INSERT INTO {fortunki.fullname}(text) VALUES (:text)", values=values
    )
    if hasattr(fortunki, "cache"):
        delattr(fortunki, "cache")
    if hasattr(fortunki, "cache_max_size"):
        delattr(fortunki, "cache_max_size")
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()):
        for _ in range(number_of_requests):
            await send_slack_request(event, client)
    # this call is necessary to clear the cache if it grew too big
    await get_recently_seen(fortunki)
    assert type(fortunki.cache) == set
    assert len(fortunki.cache) == expected_cache_size
