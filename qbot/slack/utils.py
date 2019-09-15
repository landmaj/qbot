import hashlib
import hmac

from starlette.requests import Request

from qbot.registry import registry


async def verify_signature(request: Request):
    """
    Verify the signature of the request sent from Slack with a signature
    calculated from the app's signing secret and request data.
    """

    timestamp = request.headers["X-Slack-Request-Timestamp"]
    signature = request.headers["X-Slack-Signature"]
    body = await request.body()

    req = str.encode("v0:" + str(timestamp) + ":") + body
    request_hash = (
        "v0="
        + hmac.new(
            str.encode(str(registry.SIGNING_SECRET)), req, hashlib.sha256
        ).hexdigest()
    )
    return hmac.compare_digest(request_hash, signature)
