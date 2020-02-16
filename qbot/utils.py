import hashlib
import hmac
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

from async_lru import alru_cache
from starlette.requests import Request

from qbot.consts import SLACK_URL
from qbot.core import registry

logger = logging.getLogger(__name__)


def all_modules_in_directory(directory: Path):
    return [
        f.stem
        for f in directory.glob("**/*.py")
        if f.is_file() and not f.stem.startswith("_")
    ]


def calculate_signature(timestamp, body):
    req = str.encode("v0:" + str(timestamp) + ":") + body
    return (
        "v0="
        + hmac.new(
            str.encode(str(registry.SIGNING_SECRET)), req, hashlib.sha256
        ).hexdigest()
    )


async def verify_signature(request: Request):
    """
    Verify the signature of the request sent from Slack with a signature
    calculated from the app's signing secret and request data.
    """

    timestamp = request.headers["X-Slack-Request-Timestamp"]
    signature = request.headers["X-Slack-Signature"]
    body = await request.body()
    return hmac.compare_digest(calculate_signature(timestamp, body), signature)


@alru_cache()
async def get_channel_name(channel_id: str) -> Optional[str]:
    resp = await registry.http_client.get(
        url=urljoin(SLACK_URL, "conversations.info"),
        params={"channel": channel_id},
        headers={"Authorization": f"Bearer {str(registry.SLACK_TOKEN)}"},
    )
    if not 200 <= resp.status_code < 400:
        logger.error(f"Incorrect response from Slack. Status: {resp.status}.")
        return
    body = resp.json()
    if not body["ok"]:
        error = body["error"]
        logger.error(f"Slack returned an error: {error}.")
        return
    if body["channel"]["is_im"]:
        return "im"
    elif body["channel"]["is_channel"]:
        return body["channel"]["name"]
