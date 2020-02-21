import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy import func
from vendor import facebook_scraper

from qbot.backblaze import upload_image
from qbot.command import add_command
from qbot.core import registry
from qbot.db import b2_images
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
PLUGIN_NAME = "sucharki"


@add_command("sucharek", "Psie Sucharki", channel="fortunki", aliases=["s"])
async def sucharek_cmd(message: IncomingMessage):
    result = await registry.database.fetch_one(
        b2_images.select().order_by(func.random())
    )
    if result is None:
        await send_reply(message, text="Źródełko sucharków jest suche.")
        return
    await send_reply(
        message, blocks=[Image(image_url=result["url"], alt_text="Psi Sucharek")]
    )


async def add_sucharek(image: bytes, post_id: Optional[str] = None) -> str:
    b2_image = upload_image(
        content=image,
        base_name=f"sucharek_{uuid4()}",
        plugin=PLUGIN_NAME,
        bucket=registry.b3,
    )
    download_url = registry.b3.get_download_url(b2_image.file_name)
    await registry.database.execute(
        query=b2_images.insert(),
        values={
            "plugin": PLUGIN_NAME,
            "extra": post_id,
            "external_id": b2_image.external_id,
            "file_name": b2_image.file_name,
            "hash": b2_image.hash,
            "url": download_url,
        },
    )
    return download_url


@job(300)
async def get_latest():
    current_time = datetime.utcnow()
    async for post in facebook_scraper.get_posts("psiesucharki", pages=1):
        if current_time - timedelta(hours=1) < post.time and post.image:
            result = await registry.database.fetch_one(
                b2_images.select().where(
                    (b2_images.c.plugin == PLUGIN_NAME) & (b2_images.c.extra == post.id)
                )
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
            download_url = await add_sucharek(resp.content, post.id)
            await send_message(
                OutgoingMessage(
                    channel=registry.SPAM_CHANNEL_ID,
                    thread_ts=None,
                    blocks=[
                        Text("Nowy sucharek!"),
                        Image(image_url=download_url, alt_text=post.text),
                    ],
                )
            )
