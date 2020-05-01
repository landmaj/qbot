import logging

import feedparser
from bs4 import BeautifulSoup
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
        title = latest["title"]
        header = f"*{title}*\n{latest['id']}"
        summary_html = latest["summary"].split("<!-- Easy Reader Version:")[0]
        soup = BeautifulSoup(summary_html, "html.parser")
        image = soup.find("img")
        if image is not None:
            post = (
                f"{header}\n\nToday's WTF contains images and cannot be displayed here."
            )
        else:
            summary_mrkdn = markdownify(summary_html).strip()
            post = f"{header}\n\n{summary_mrkdn}"
        await send_message(SimpleMessage(channel=registry.CHANNEL_COMICS, text=post))
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
