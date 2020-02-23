import logging

import feedparser
from requests_html import HTML

from qbot.core import registry
from qbot.db import plugin_storage
from qbot.message import Image, OutgoingMessage, Text, send_message
from qbot.scheduler import job

PLUGIN_NAME = "classic_programmer_paintings"
LATEST_COMIC_KEY = "latest_comic"

logger = logging.getLogger(__name__)


@job(3600)
async def classic_programmer_paintings():
    last_seen_comic = await registry.database.fetch_val(
        plugin_storage.select().where(
            (plugin_storage.c.plugin == PLUGIN_NAME)
            & (plugin_storage.c.key == LATEST_COMIC_KEY)
        ),
        column=plugin_storage.c.data,
    )
    try:
        resp = await registry.http_client.get(
            "https://classicprogrammerpaintings.com/rss"
        )
    except Exception:
        logger.exception(
            "Failed to retrieve latest Classic Programmer Paintings comic."
        )
        return
    if not 200 <= resp.status_code < 400:
        logger.error(
            f"Incorrect response from Classic Programmer Paintings. Status: {resp.status_code}"
        )
        return
    rss = feedparser.parse(resp.text)
    latest = rss.entries[0]
    img = latest["link"].replace("/post/", "/image/")
    if latest["title"] != last_seen_comic:
        parsed_html = HTML(html=latest["description"])
        text = "\n".join([x.text for x in parsed_html.find("p")])
        await send_message(
            OutgoingMessage(
                channel=registry.CHANNEL_COMICS,
                thread_ts=None,
                blocks=[
                    Text(f"https://classicprogrammerpaintings.com - {text}"),
                    Image(image_url=img, alt_text=latest["title"]),
                ],
            )
        )
        if last_seen_comic is None:
            await registry.database.execute(
                plugin_storage.insert(),
                values={
                    "plugin": PLUGIN_NAME,
                    "key": LATEST_COMIC_KEY,
                    "data": latest["title"],
                },
            )
        else:
            await registry.database.execute(
                plugin_storage.update().where(
                    (plugin_storage.c.plugin == PLUGIN_NAME)
                    & (plugin_storage.c.key == LATEST_COMIC_KEY)
                ),
                values={"data": latest["title"]},
            )
