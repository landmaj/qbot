import hashlib
import hmac
import os

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse

app = Starlette()

GIT_REV = os.environ.get("GIT_REV", "N/A")
SIGNING_SECRET = os.environ.get("Q_SIGNING_SECRET")


@app.route("/")
async def index(request: Request):
    return PlainTextResponse(f"Qbot::{GIT_REV[:8]}")


@app.route("/slack", methods=["POST"])
async def slack_handler(request: Request):
    try:
        if not await verify_signature(request):
            return PlainTextResponse("Incorrect signature.", 403)
    except Exception:
        return PlainTextResponse("Could not verify signature.", 400)

    data = await request.json()
    if "challenge" in data:
        return PlainTextResponse(data["challenge"], 200)
    return PlainTextResponse("OK", 200)


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
        "v0=" + hmac.new(str.encode(SIGNING_SECRET), req, hashlib.sha256).hexdigest()
    )
    return hmac.compare_digest(request_hash, signature)
