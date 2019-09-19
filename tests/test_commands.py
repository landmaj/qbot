import json
import time
from unittest.mock import patch

import pytest
from asynctest import CoroutineMock

from qbot.slack.utils import calculate_signature


@pytest.mark.parametrize("message_text", ["!ping", "!help", "!uptime", "!top"])
def test_command(client, message_text):
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
    timestamp = time.time()
    data = json.dumps(event).encode("utf-8")
    signature = calculate_signature(timestamp, data)
    with patch("qbot.slack.message.send_message", new=CoroutineMock()) as mock:
        response = client.post(
            "/slack",
            headers={
                "X-Slack-Request-Timestamp": str(timestamp),
                "X-Slack-Signature": signature,
            },
            data=data,
        )
        mock.assert_called_once()
    assert response.status_code == 200
    assert response.text == "OK"
