from unittest.mock import ANY, patch

import pytest
from asynctest import CoroutineMock

from qbot.core import registry
from qbot.db import fortunki
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
    await registry.database.execute_many(query=fortunki.insert(), values=values)
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
    await registry.database.execute_many(query=fortunki.insert(), values=values)
    fortunki.cache = set()
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        mock.assert_called_once_with(ANY, text=ANY)
    assert response.status_code == 200
    assert response.text == "OK"
    assert type(fortunki.cache) == set
    assert len(fortunki.cache) == 1


@pytest.mark.asyncio
async def test_get_recently_seen_single_item(client):
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
    await registry.database.execute(query=fortunki.insert(), values={"text": "1"})
    if hasattr(fortunki, "cache"):
        delattr(fortunki, "cache")
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        await send_slack_request(event, client)
        await send_slack_request(event, client)
        first = mock.call_args_list[0][1]["text"]
        second = mock.call_args_list[1][1]["text"]
        assert first == second != "Nie ma fortunek :("
    assert type(fortunki.cache) == set
    assert len(fortunki.cache) == 0


@pytest.mark.asyncio
async def test_get_recently_seen_three_items(client):
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
    values = [{"text": "1"}, {"text": "2"}, {"text": "3"}]
    await registry.database.execute_many(query=fortunki.insert(), values=values)
    if hasattr(fortunki, "cache"):
        delattr(fortunki, "cache")
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        for _ in range(10):
            for _ in range(3):
                await send_slack_request(event, client)
            first = mock.call_args_list[0][1]["text"]
            second = mock.call_args_list[1][1]["text"]
            third = mock.call_args_list[2][1]["text"]
            assert first != second != third != "Nie ma fortunek :("
    assert type(fortunki.cache) == set
    assert len(fortunki.cache) == 2


@pytest.mark.parametrize(
    ["number_of_inputs", "expected_cache_size", "number_of_requests"],
    [
        (0, 0, 1),
        (0, 0, 2),
        (1, 0, 1),
        (1, 0, 2),
        (2, 1, 1),
        (2, 1, 2),
        (3, 1, 1),
        (3, 2, 2),
        (3, 1, 3),
        (4, 1, 1),
        (4, 2, 2),
        (4, 3, 3),
        (4, 1, 4),
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
    await registry.database.execute_many(query=fortunki.insert(), values=values)
    if hasattr(fortunki, "cache"):
        delattr(fortunki, "cache")
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()):
        for _ in range(number_of_requests):
            await send_slack_request(event, client)
    assert type(fortunki.cache) == set
    assert len(fortunki.cache) == expected_cache_size
