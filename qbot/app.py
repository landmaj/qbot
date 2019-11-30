from sentry_sdk import capture_exception
from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from qbot import metrics
from qbot.core import registry
from qbot.slack.event import process_slack_event
from qbot.slack.utils import verify_signature

app = Starlette()


@app.route("/")
async def index(request: Request):
    metrics.incr("endpoint.index")
    return PlainTextResponse(f"Qbot::{registry.REVISION:.8}")


@app.route("/ping")
async def ping(request: Request):
    metrics.incr("endpoint.ping")
    return PlainTextResponse("pong")


@app.on_event("startup")
async def setup_registry():
    await registry.setup(app)


@app.on_event("shutdown")
async def teardown_registry():
    await registry.teardown()


@app.route("/slack", methods=["POST"])
async def slack_handler(request: Request):
    try:
        if not await verify_signature(request):
            metrics.incr("endpoint.slack.invalid")
            return PlainTextResponse("Incorrect signature.", 403)
    except Exception as exc:
        capture_exception(exc)
        metrics.incr("endpoint.slack.invalid")
        return PlainTextResponse("Could not verify signature.", 400)
    metrics.incr("endpoint.slack.valid")

    data = await request.json()
    if "challenge" in data:
        return PlainTextResponse(data["challenge"])

    task = BackgroundTask(
        process_slack_event, event=data["event"], event_id=data["event_id"]
    )
    return PlainTextResponse("OK", background=task)
