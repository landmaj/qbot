import logging
from typing import Optional

from qbot.backblaze import upload_image
from qbot.command import add_command
from qbot.core import registry
from qbot.cron import cron_job
from qbot.db import b2_images
from qbot.message import (
    Image,
    IncomingMessage,
    OutgoingMessage,
    Text,
    send_message,
    send_random_image,
)
from vendor import facebook_scraper

logger = logging.getLogger(__name__)
PLUGIN_NAME = "sucharki"


@add_command("sucharek", "Psie Sucharki", channel="fortunki", aliases=["s"])
async def sucharek_cmd(message: IncomingMessage):
    await send_random_image(message, PLUGIN_NAME, "Psi Sucharek")


async def add_sucharek(image: bytes, post_id: Optional[str] = None) -> Optional[str]:
    b2_image = await upload_image(
        content=image, plugin=PLUGIN_NAME, bucket=registry.b3, extra=post_id
    )
    if b2_image is None:
        return
    return b2_image.url


@cron_job
async def get_latest():
    async for post in facebook_scraper.get_posts("psiesucharki", pages=1):
        if post.image is None:
            continue
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
            logger.error(f"Incorrect response from Facebook. Status: {resp.status}.")
            continue
        download_url = await add_sucharek(resp.content, post.id)
        if download_url is None:
            logger.error("Failed to upload a new sucharek.")
        await send_message(
            OutgoingMessage(
                channel=registry.CHANNEL_COMICS,
                thread_ts=None,
                blocks=[
                    Text("Nowy sucharek!"),
                    Image(image_url=download_url, alt_text=post.text),
                ],
            )
        )
