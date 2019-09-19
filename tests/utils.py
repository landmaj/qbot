import json
from time import time

from async_asgi_testclient import TestClient

from qbot.slack.utils import calculate_signature


async def send_slack_request(event: dict, client: TestClient):
    timestamp = time()
    data = json.dumps(event).encode("utf-8")
    signature = calculate_signature(timestamp, data)
    return await client.post(
        "/slack",
        headers={
            "X-Slack-Request-Timestamp": str(timestamp),
            "X-Slack-Signature": signature,
        },
        data=data,
    )
