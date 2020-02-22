from unittest.mock import patch

import pytest
from asynctest import CoroutineMock

from tests.utils import send_slack_request


@pytest.mark.parametrize(
    "message_text", ["!ping", "!help", "!uptime", "!top", "!about"]
)
@pytest.mark.asyncio
async def test_command(aresponses, client, message_text):
    event = {
        "token": "z26uFbvR1xHJEdHE1OQiO6t8",
        "team_id": "T061EG9RZ",
        "api_app_id": "A0FFV41KK",
        "event": {
            "type": "message",
            "channel": "C2147483705",
            "user": "U2147483697",
            "text": message_text,
            "ts": "1355517523.000005",
        },
        "type": "event_callback",
        "authed_users": ["U061F7AUR"],
        "event_id": "Ev9UQ52YNA",
        "event_time": 1234567890,
    }
    aresponses.add(
        "slack.com",
        "/api/conversations.info",
        "get",
        aresponses.Response(text="error", status=401),
    )
    with patch("qbot.message.send_message", new=CoroutineMock()) as mock:
        response = await send_slack_request(event, client)
        mock.assert_called_once()
    assert response.status_code == 200
    assert response.text == "OK"
