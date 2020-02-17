import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urljoin

from asyncpg import UniqueViolationError
from vendor import facebook_scraper

from qbot.app import app
from qbot.command import add_command
from qbot.core import registry
from qbot.db import add_recently_seen, query_with_recently_seen, sucharki
from qbot.message import (
    Image,
    IncomingMessage,
    OutgoingMessage,
    Text,
    send_message,
    send_reply,
)
from qbot.scheduler import job

logger = logging.getLogger(__name__)


@add_command("sucharek", "`!sucharek [-- ID]`", channel="fortunki", aliases=["s"])
async def sucharek_cmd(message: IncomingMessage):
    identifier = None
    if message.text:
        try:
            identifier = int(message.text)
        except ValueError:
            await send_reply(message, text="Niepoprawne ID.")
            return
    result = await query_with_recently_seen(sucharki, identifier)
    if result is None:
        await send_reply(message, text="Źródełko sucharków jest suche.")
        return
    identifier = result["id"]
    await send_reply(
        message,
        blocks=[
            Image(
                image_url=urljoin(
                    registry.ROOT_DOMAIN,
                    app.url_path_for("sucharek", sucharek_id=identifier),
                ),
                alt_text="Psi Sucharek",
            )
        ],
    )
    await add_recently_seen(sucharki, result["id"])


async def add_sucharek(image: bytes, post_id: Optional[str] = None) -> int:
    sha256 = hashlib.sha256()
    sha256.update(image)
    try:
        async with registry.database.transaction():
            return await registry.database.execute(
                query=sucharki.insert(),
                values={"image": image, "digest": sha256.digest(), "post_id": post_id},
            )
    except UniqueViolationError:
        result = await registry.database.fetch_one(
            sucharki.select().where(sucharki.c.digest == sha256.digest())
        )
        return result["id"]


@job(3600)
async def get_latest():
    current_time = datetime.utcnow()
    async for post in facebook_scraper.get_posts("psiesucharki", pages=1):
        if current_time - timedelta(hours=24) < post.time and post.image:
            result = await registry.database.fetch_one(
                sucharki.select().where(sucharki.c.post_id == post.id)
            )
            if result is not None:
                continue
            try:
                resp = await registry.http_client.get(post.image)
            except Exception:
                logger.exception("Exception during Facebook image request.")
                continue
            if not 200 <= resp.status_code < 400:
                logger.error(
                    f"Incorrect response from Facebook. Status: {resp.status}."
                )
                continue
            identifier = await add_sucharek(resp.content, post.id)
            await send_message(
                OutgoingMessage(
                    channel=registry.SPAM_CHANNEL_ID,
                    thread_ts=None,
                    blocks=[
                        Text("Nowy sucharek!"),
                        Image(
                            image_url=urljoin(
                                registry.ROOT_DOMAIN,
                                app.url_path_for("sucharek", sucharek_id=identifier),
                            ),
                            alt_text=post.text,
                        ),
                    ],
                )
            )
