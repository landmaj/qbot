import logging

from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

from qbot.core import registry
from qbot.event import process_slack_event
from qbot.utils import verify_signature


class Index(HTTPEndpoint):
    async def get(self, request: Request) -> Response:
        return PlainTextResponse("qbot")

    async def post(self, request: Request) -> Response:
        try:
            if not await verify_signature(request):
                return PlainTextResponse("Incorrect signature.", 403)
        except Exception:
            logging.exception("Could not verify signature.")
            return PlainTextResponse("Could not verify signature.", 400)

        data = await request.json()
        if "challenge" in data:
            return PlainTextResponse(data["challenge"])

        task = BackgroundTask(
            process_slack_event, event=data["event"], event_id=data["event_id"]
        )
        return PlainTextResponse("OK", background=task)


app = Starlette(routes=[Route("/", Index)])


@app.on_event("startup")
async def setup_registry():
    await registry.setup()


@app.on_event("shutdown")
async def teardown_registry():
    await registry.teardown()
