from unittest.mock import ANY, patch

import pytest
from asynctest import CoroutineMock

from qbot.core import registry
from qbot.db import fortunki
from tests.utils import send_slack_request


@pytest.mark.asyncio
async def test_no_fortunkas(client):
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
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        mock.assert_called_once_with(ANY, text="Nie ma fortunek :(")
    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_fortunka_dodaj(client):
    event = {
        "event": {
            "type": "message",
            "channel": "C2147483705",
            "user": "U2147483697",
            "text": "!fortunka dodaj -- qwerty",
            "ts": "1355517523.000005",
        },
        "event_id": "Ev9UQ52YNA",
    }
    count_before = await registry.database.execute(
        query=f"SELECT COUNT(*) FROM {fortunki.fullname}"
    )
    assert count_before == 0
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        mock.assert_called_once_with(ANY, text=ANY)
    count_after = await registry.database.execute(
        query=f"SELECT COUNT(*) FROM {fortunki.fullname}"
    )
    assert count_after == 1
    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_fortunka_dodaj_empty_message(client):
    event = {
        "event": {
            "type": "message",
            "channel": "C2147483705",
            "user": "U2147483697",
            "text": "!fortunka dodaj",
            "ts": "1355517523.000005",
        },
        "event_id": "Ev9UQ52YNA",
    }
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        mock.assert_called_once_with(ANY, text="Pustych fortunek nie dodaję!")
    count_after = await registry.database.execute(
        query=f"SELECT COUNT(*) FROM {fortunki.fullname}"
    )
    assert count_after == 0
    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_fortunka_dodaj_unique_violation(client):
    event = {
        "event": {
            "type": "message",
            "channel": "C2147483705",
            "user": "U2147483697",
            "text": "!fortunka dodaj -- qwerty",
            "ts": "1355517523.000005",
        },
        "event_id": "Ev9UQ52YNA",
    }
    await registry.database.execute(
        query=f"INSERT INTO {fortunki.fullname}(text) VALUES ('qwerty')"
    )
    count_before = await registry.database.execute(
        query=f"SELECT COUNT(*) FROM {fortunki.fullname}"
    )
    assert count_before == 1
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        mock.assert_called_once_with(ANY, text="Taka fortunka już istnieje.")
    count_after = await registry.database.execute(
        query=f"SELECT COUNT(*) FROM {fortunki.fullname}"
    )
    assert count_after == 1
    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_fortunka(client):
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
    await registry.database.execute(
        query=f"INSERT INTO {fortunki.fullname}(text) VALUES ('qwerty')"
    )
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        mock.assert_called_once_with(ANY, text="qwerty")
    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.parametrize("identifier", ["not an integer", "2137.7312"])
@pytest.mark.asyncio
async def test_fortunka_id_not_an_integer(client, identifier):
    event = {
        "event": {
            "type": "message",
            "channel": "C2147483705",
            "user": "U2147483697",
            "text": f"!fortunka -- {identifier}",
            "ts": "1355517523.000005",
        },
        "event_id": "Ev9UQ52YNA",
    }
    await registry.database.execute(
        query=f"INSERT INTO {fortunki.fullname}(text) VALUES ('qwerty')"
    )
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        mock.assert_called_once_with(ANY, text=f"Niepoprawne ID.")
    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_fortunka_id_not_an_integer(client):
    event = {
        "event": {
            "type": "message",
            "channel": "C2147483705",
            "user": "U2147483697",
            "text": f"!fortunka -- 2137",
            "ts": "1355517523.000005",
        },
        "event_id": "Ev9UQ52YNA",
    }
    await registry.database.execute(
        query=f"INSERT INTO {fortunki.fullname}(text) VALUES ('qwerty')"
    )
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        mock.assert_called_once_with(ANY, text=f"Nie ma fortunki o ID 2137.")
    assert response.status_code == 200
    assert response.text == "OK"
