import logging

from qbot.core import registry
from qbot.db import plugin_storage
from qbot.message import Image, OutgoingMessage, Text, send_message
from qbot.scheduler import job

PLUGIN_NAME = "xkcd"
LATEST_COMIC_KEY = "latest_comic"

logger = logging.getLogger(__name__)


@job(3600)
async def xkcd():
    last_seen_comic = await registry.database.fetch_val(
        plugin_storage.select().where(
            (plugin_storage.c.plugin == PLUGIN_NAME)
            & (plugin_storage.c.key == LATEST_COMIC_KEY)
        ),
        column=plugin_storage.c.data,
    )
    try:
        resp = await registry.http_client.get("https://xkcd.com/info.0.json")
    except Exception:
        logger.exception("Failed to retrieve latest XKCD comic.")
        return
    if not 200 <= resp.status_code < 400:
        logger.error(f"Incorrect response from XKCD. Status: {resp.status_code}")
        return
    data = resp.json()
    if data["num"] != last_seen_comic:
        await send_message(
            OutgoingMessage(
                channel=registry.SPAM_CHANNEL_ID,
                thread_ts=None,
                blocks=[
                    Text(f"https://xkcd.com - {data['safe_title']}"),
                    Image(image_url=data["img"], alt_text=data["alt"]),
                ],
            )
        )
        if last_seen_comic is None:
            await registry.database.execute(
                plugin_storage.insert(),
                values={
                    "plugin": PLUGIN_NAME,
                    "key": LATEST_COMIC_KEY,
                    "data": data["num"],
                },
            )
        else:
            await registry.database.execute(
                plugin_storage.update().where(
                    (plugin_storage.c.plugin == PLUGIN_NAME)
                    & (plugin_storage.c.key == LATEST_COMIC_KEY)
                ),
                values={"data": data["num"]},
            )
