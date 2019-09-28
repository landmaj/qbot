from unittest.mock import ANY, patch

import pytest
from asynctest import CoroutineMock
from sqlalchemy import func, select

from qbot.core import registry
from qbot.db import fortunki
from qbot.slack.message import TextWithButton
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
        mock.assert_called_once_with(ANY, text="O cokolwiek prosiłeś - nie istnieje.")
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
    count_before = await registry.database.fetch_val(
        select([func.count()]).select_from(fortunki)
    )
    assert count_before == 0
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        identifier = await registry.database.fetch_val(
            query=fortunki.select(), column="id"
        )
        mock.assert_called_once_with(ANY, text=f"Fortunka {identifier} dodana!")
    count_after = await registry.database.fetch_val(
        select([func.count()]).select_from(fortunki)
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
    count_after = await registry.database.fetch_val(
        select([func.count()]).select_from(fortunki)
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
    await registry.database.execute(query=fortunki.insert(), values={"text": "qwerty"})
    count_before = await registry.database.fetch_val(
        select([func.count()]).select_from(fortunki)
    )
    assert count_before == 1
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        mock.assert_called_once_with(ANY, text="Taka fortunka już istnieje.")
    count_after = await registry.database.fetch_val(
        select([func.count()]).select_from(fortunki)
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
    identifier = await registry.database.execute(
        query=fortunki.insert(), values={"text": "qwerty"}
    )
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        mock.assert_called_once_with(
            ANY, blocks=[TextWithButton(text="qwerty", button_text=str(identifier))]
        )
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
    await registry.database.execute(query=fortunki.insert(), values={"text": "qwerty"})
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
    await registry.database.execute(query=fortunki.insert(), values={"text": "qwerty"})
    with patch("qbot.slack.plugin_fortunka.send_reply", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        mock.assert_called_once_with(ANY, text=f"O cokolwiek prosiłeś - nie istnieje.")
    assert response.status_code == 200
    assert response.text == "OK"
