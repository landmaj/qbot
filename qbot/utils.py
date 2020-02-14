import hashlib
import hmac
from pathlib import Path

from starlette.requests import Request

from qbot.core import registry


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
