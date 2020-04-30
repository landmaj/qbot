import logging

import feedparser
from vendor.markdownify import markdownify

from qbot.core import registry
from qbot.db import plugin_storage
from qbot.message import SimpleMessage, send_message
from qbot.scheduler import job

PLUGIN_NAME = "wtf"
LATEST_COMIC_KEY = "latest_comic"

logger = logging.getLogger(__name__)


@job(3600)
async def wtf():
    last_seen_comic = await registry.database.fetch_val(
        plugin_storage.select().where(
            (plugin_storage.c.plugin == PLUGIN_NAME)
            & (plugin_storage.c.key == LATEST_COMIC_KEY)
        ),
        column=plugin_storage.c.data,
    )
    try:
        resp = await registry.http_client.get(
            "http://syndication.thedailywtf.com/TheDailyWtf"
        )
    except Exception:
        logger.exception("Failed to retrieve latest The Daily WTF comic.")
        return
    if not 200 <= resp.status_code < 400:
        logger.error(
            f"Incorrect response from The Daily WTF. Status: {resp.status_code}"
        )
        return
    rss = feedparser.parse(resp.text)
    latest = rss.entries[0]
    if latest["id"] != last_seen_comic:
        summary_html = latest["summary"].split("<!-- Easy Reader Version:")[0]
        summary_mrkdn = markdownify(summary_html).strip()
        await send_message(
            SimpleMessage(channel=registry.CHANNEL_COMICS, text=summary_mrkdn)
        )
        if last_seen_comic is None:
            await registry.database.execute(
                plugin_storage.insert(),
                values={
                    "plugin": PLUGIN_NAME,
                    "key": LATEST_COMIC_KEY,
                    "data": latest["id"],
                },
            )
        else:
            await registry.database.execute(
                plugin_storage.update().where(
                    (plugin_storage.c.plugin == PLUGIN_NAME)
                    & (plugin_storage.c.key == LATEST_COMIC_KEY)
                ),
                values={"data": latest["id"]},
            )
