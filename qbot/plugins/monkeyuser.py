import logging

import feedparser
from requests_html import HTML

from qbot.core import registry
from qbot.db import plugin_storage
from qbot.message import Image, OutgoingMessage, Text, send_message
from qbot.scheduler import job

PLUGIN_NAME = "monkey_user"
LATEST_COMIC_KEY = "latest_comic"

logger = logging.getLogger(__name__)


@job(3600)
async def monkeyuser():
    last_seen_comic = await registry.database.fetch_val(
        plugin_storage.select().where(
            (plugin_storage.c.plugin == PLUGIN_NAME)
            & (plugin_storage.c.key == LATEST_COMIC_KEY)
        ),
        column=plugin_storage.c.data,
    )
    try:
        resp = await registry.http_client.get("https://www.monkeyuser.com/feed.xml")
    except Exception:
        logger.exception("Failed to retrieve latest monkeyuser comic.")
        return
    if not 200 <= resp.status_code < 400:
        logger.error(f"Incorrect response from monkeyuser. Status: {resp.status_code}")
        return
    rss = feedparser.parse(resp.text)
    summary = rss.entries[0]["summary"]
    parsed_html = HTML(html=summary)
    data = parsed_html.find("img", first=True).attrs
    if data["alt"] != last_seen_comic:
        await send_message(
            OutgoingMessage(
                channel=registry.SPAM_CHANNEL_ID,
                thread_ts=None,
                blocks=[
                    Text(data["alt"]),
                    Image(image_url=data["src"], alt_text=data["title"]),
                ],
            )
        )
        if last_seen_comic is None:
            await registry.database.execute(
                plugin_storage.insert(),
                values={
                    "plugin": PLUGIN_NAME,
                    "key": LATEST_COMIC_KEY,
                    "data": data["alt"],
                },
            )
        else:
            await registry.database.execute(
                plugin_storage.update().where(
                    (plugin_storage.c.plugin == PLUGIN_NAME)
                    & (plugin_storage.c.key == LATEST_COMIC_KEY)
                ),
                values={"data": data["alt"]},
            )
