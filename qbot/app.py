import hashlib
import hmac

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from qbot.slack_commands import *  # noqa
from qbot.slack_handlers import *  # noqa
from qbot.slack_utils import event_type_mapping

app = Starlette()


@app.route("/")
async def index(request: Request):
    return PlainTextResponse(f"Qbot::{registry.REVISION}")


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

    slack_event = data["event"]
    event_type_mapping[slack_event["type"]](slack_event)

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
        "v0="
        + hmac.new(str.encode(registry.SIGNING_SECRET), req, hashlib.sha256).hexdigest()
    )
    return hmac.compare_digest(request_hash, signature)
