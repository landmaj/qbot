import logging

import feedparser
from requests_html import HTML

from qbot.core import registry
from qbot.cron import cron_job
from qbot.db import plugin_storage
from qbot.message import Image, OutgoingMessage, Text, send_message

PLUGIN_NAME = "commitstrip"
LATEST_COMIC_KEY = "latest_comic"

logger = logging.getLogger(__name__)


@cron_job
async def commitstrip():
    last_seen_comic = await registry.database.fetch_val(
        plugin_storage.select().where(
            (plugin_storage.c.plugin == PLUGIN_NAME)
            & (plugin_storage.c.key == LATEST_COMIC_KEY)
        ),
        column=plugin_storage.c.data,
    )
    try:
        resp = await registry.http_client.get("http://www.commitstrip.com/en/feed/")
    except Exception:
        logger.exception("Failed to retrieve latest CommitStrip comic.")
        return
    if not 200 <= resp.status_code < 400:
        logger.error(f"Incorrect response from CommitStrip. Status: {resp.status_code}")
        return
    rss = feedparser.parse(resp.text)
    latest = rss.entries[0]
    if latest["title"] != last_seen_comic:
        parsed_html = HTML(html=latest["content"][0]["value"])
        data = parsed_html.find("img", first=True).attrs
        await send_message(
            OutgoingMessage(
                channel=registry.CHANNEL_COMICS,
                thread_ts=None,
                blocks=[
                    Text(f"https://www.commitstrip.com - {latest['title']}"),
                    Image(image_url=data["src"], alt_text=latest["title"]),
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
