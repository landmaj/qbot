import logging
from typing import Optional

from bs4 import BeautifulSoup

from qbot.backblaze import upload_image
from qbot.command import add_command
from qbot.core import registry
from qbot.db import b2_images, nosacze
from qbot.message import (
    Image,
    IncomingMessage,
    OutgoingMessage,
    Text,
    send_message,
    send_random_image,
    send_reply,
)
from qbot.plugins.excuse import bot_malfunction
from qbot.scheduler import job

logger = logging.getLogger(__name__)
PLUGIN_NAME_NOSACZE = "nosacze"


@add_command(
    "janusz",
    "Losowe memiszcze z janusznosacz.pl.",
    channel="fortunki",
    aliases=["j", "janush"],
)
async def janusz_cmd(message: IncomingMessage):
    while True:
        resp = await registry.http_client.get("http://www.janusznosacz.pl/losuj")
        if not 200 <= resp.status_code < 400:
            logger.error(
                f"Incorrect response from janusznosacz.pl. Status: {resp.status}."
            )
            await bot_malfunction(message)
            return
        # random image sometimes returns an error and redirects to the home page
        if resp.url.path == "/":
            continue
        body = resp.text
        break

    soup = BeautifulSoup(body, "html.parser")
    try:
        image_url = (
            soup.find("div", {"class": "img-inner-box"}).find("a").find("img")["src"]
        )
        alt_text = (
            soup.find("div", {"class": "image-box"})
            .find("h2")
            .get_text()
            .strip()
            .split("\n")[0]
        )
    except Exception:
        logger.exception("Could not extract image source from the page.")
        await bot_malfunction(message)
        return
    await send_reply(message, blocks=[Image(image_url, alt_text)])


@add_command("nosacz", "Nieświeże memy od somsiada.", channel="fortunki", aliases=["n"])
async def nosacz_cmd(message: IncomingMessage):
    await send_random_image(message, PLUGIN_NAME_NOSACZE, "Nosacz sundajski")


@add_command(
    "nosacz dodaj",
    "`!nosacz dodaj -- https://example.com/image.jpg`",
    channel="fortunki",
    safe_to_fix=False,
)
async def nosacz_dodaj_cmd(message: IncomingMessage):
    await send_reply(message, text="`raise NotImplementedError`")


async def add_nosacz(url: str) -> Optional[str]:
    resp = await registry.http_client.get(url)
    b2_image = upload_image(
        content=resp.content, plugin=PLUGIN_NAME_NOSACZE, bucket=registry.b3
    )
    if b2_image is None:
        await send_message(
            OutgoingMessage(
                channel=registry.SPAM_CHANNEL_ID,
                thread_ts=None,
                blocks=[Text(f"Nie udało się dodać nosacza: {url}")],
            )
        )
        return
    await registry.database.execute(
        query=b2_images.insert(),
        values={
            "plugin": PLUGIN_NAME_NOSACZE,
            "file_name": b2_image.file_name,
            "hash": b2_image.hash,
            "url": b2_image.url,
        },
    )
    return b2_image.url


@job()
async def upload_existing():
    images = await registry.database.fetch_all(nosacze.select())
    for img in images:
        await add_nosacz(img["url"])
