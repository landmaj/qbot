import hashlib
import hmac

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse

app = Starlette()

SIGNING_SECRET = ""


@app.route("/slack")
async def slack_handler(request: Request):
    if not await verify_signature(request):
        return PlainTextResponse("Incorrect signature.", 403)

    data = await request.json()
    if "challenge" in data:
        return PlainTextResponse(data["challenge"], 200)
    return PlainTextResponse("OK", 200)


async def verify_signature(request: Request):
    """
    Verify the signature of the request sent from Slack with a signature
    calculated from the app's signing secret and request data.
    """

    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")
    body = await request.body()

    req = str.encode("v0:" + str(timestamp) + ":") + body
    request_hash = (
        "v0=" + hmac.new(str.encode(SIGNING_SECRET), req, hashlib.sha256).hexdigest()
    )
    return hmac.compare_digest(request_hash, signature)
