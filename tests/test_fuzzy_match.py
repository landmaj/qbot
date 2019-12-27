from unittest.mock import ANY, patch

import pytest
from asynctest import CoroutineMock

from tests.utils import send_slack_request


@pytest.mark.asyncio
async def test_no_match(client):
    event = {
        "event": {
            "type": "message",
            "channel": "C2147483705",
            "user": "U2147483697",
            "text": "!incorrect",
            "ts": "1355517523.000005",
        },
        "event_id": "Ev9UQ52YNA",
    }
    with patch("qbot.slack.event.send_reply", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        mock.assert_called_once_with(ANY, text="Nieznane polecenie: incorrect")
    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_simple_typo(client):
    event = {
        "event": {
            "type": "message",
            "channel": "C2147483705",
            "user": "U2147483697",
            "text": "!halp",
            "ts": "1355517523.000005",
        },
        "event_id": "Ev9UQ52YNA",
    }
    with patch("qbot.slack.event.send_reply", new=CoroutineMock()) as event_mock:
        with patch("qbot.slack.command.send_reply", new=CoroutineMock()) as cmd_mock:
            response = await send_slack_request(event, client)
            event_mock.assert_called_once_with(ANY, text="FTFY: halp -> help")
            cmd_mock.assert_called_once_with(ANY, text=ANY)
    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_not_safe_to_fix_typo(client):
    event = {
        "event": {
            "type": "message",
            "channel": "C2147483705",
            "user": "U2147483697",
            "text": "!forunka dodaj",
            "ts": "1355517523.000005",
        },
        "event_id": "Ev9UQ52YNA",
    }
    with patch("qbot.slack.event.send_reply", new=CoroutineMock()) as event_mock:
        with patch("qbot.slack.command.send_reply", new=CoroutineMock()) as cmd_mock:
            response = await send_slack_request(event, client)
            event_mock.assert_called_once_with(
                ANY,
                text="Jestem w 96% pewien, że chodziło o `fortunka dodaj`. Spróbuj ponownie.",
            )
            cmd_mock.assert_not_called()
    assert response.status_code == 200
    assert response.text == "OK"
