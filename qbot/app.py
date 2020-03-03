import json
import logging

from pydantic import ValidationError
from sqlalchemy import func
from starlette.applications import Starlette
from starlette.authentication import requires
from starlette.background import BackgroundTask
from starlette.endpoints import HTTPEndpoint
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request
from starlette.responses import (
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
)
from starlette.routing import Route

from qbot.auth import BasicAuthBackend
from qbot.core import registry
from qbot.db import b2_images
from qbot.event import process_slack_event
from qbot.message import OutgoingMessage, TextWithLink, send_message
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


async def random_image(request: Request) -> Response:
    plugin = request.path_params["plugin"]
    result = await registry.database.fetch_one(
        b2_images.select()
        .order_by(func.random())
        .where((b2_images.c.plugin == plugin) & (b2_images.c.deleted == False))
    )
    if result is None:
        return Response("Not Found", 404)
    return RedirectResponse(result["url"])


@requires("authenticated")
async def login(request: Request) -> Response:
    return PlainTextResponse(f"Hello, {request.user.display_name}")


@requires("authenticated")
async def news(request: Request) -> Response:
    try:
        block = TextWithLink(**await request.json())
    except ValidationError as exc:
        return JSONResponse(json.loads(exc.json()), 400)
    except Exception:
        logging.exception(
            f"Could not deserialize or validate JSON in '{news.__name__}' "
            f"from '{request.user.display_name}'."
        )
        return PlainTextResponse("Bad Request", 400)
    return PlainTextResponse(
        "OK",
        background=BackgroundTask(
            send_message,
            message=OutgoingMessage(
                channel=registry.CHANNEL_NEWS, thread_ts=None, blocks=[block]
            ),
        ),
    )


app = Starlette(
    routes=[
        Route("/", Index),
        Route("/login", login),
        Route("/news", news, methods=["POST"]),
        Route("/image/{plugin}", random_image),
    ],
    middleware=[Middleware(AuthenticationMiddleware, backend=BasicAuthBackend())],
)


@app.on_event("startup")
async def setup_registry():
    await registry.setup()


@app.on_event("shutdown")
async def teardown_registry():
    await registry.teardown()
