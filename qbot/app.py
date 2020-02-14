from sentry_sdk import capture_exception
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.endpoints import HTTPEndpoint
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from qbot.core import registry
from qbot.event import process_slack_event
from qbot.utils import verify_signature


class Index(HTTPEndpoint):
    async def get(self, request: Request):
        return PlainTextResponse("qbot")

    async def post(self, request: Request):
        try:
            if not await verify_signature(request):
                return PlainTextResponse("Incorrect signature.", 403)
        except Exception as exc:
            capture_exception(exc)
            return PlainTextResponse("Could not verify signature.", 400)

        data = await request.json()
        if "challenge" in data:
            return PlainTextResponse(data["challenge"])

        task = BackgroundTask(
            process_slack_event, event=data["event"], event_id=data["event_id"]
        )
        return PlainTextResponse("OK", background=task)


app = Starlette(
    routes=[Route("/", Index)], middleware=[Middleware(SentryAsgiMiddleware)]
)


@app.on_event("startup")
async def setup_registry():
    await registry.setup()
    import qbot.plugins  # noqa


@app.on_event("shutdown")
async def teardown_registry():
    await registry.teardown()
