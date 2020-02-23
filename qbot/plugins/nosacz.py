import logging
from typing import Optional

from bs4 import BeautifulSoup

from qbot.backblaze import upload_image
from qbot.command import add_command
from qbot.core import registry
from qbot.db import b2_images, b2_images_interim, b2_images_interim_insert, count
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
PLUGIN_NAME_FEELS = "feels"


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
    response = await b2_images_interim_insert(PLUGIN_NAME_NOSACZE, message.text)
    await send_reply(message, text=response)


@add_command("feel", "Smutne memy od somsiada.", channel="fortunki")
async def feel_cmd(message: IncomingMessage):
    await send_random_image(message, PLUGIN_NAME_FEELS, "Smutny nosacz sundajski")


@add_command(
    "feel dodaj",
    "`!feel dodaj -- https://example.com/image.jpg`",
    channel="fortunki",
    safe_to_fix=False,
)
async def feel_dodaj_cmd(message: IncomingMessage):
    response = await b2_images_interim_insert(PLUGIN_NAME_FEELS, message.text)
    await send_reply(message, text=response)


async def _upload_image(url: str, plugin: str) -> Optional[str]:
    resp = await registry.http_client.get(url)
    b2_image = await upload_image(
        content=resp.content, plugin=plugin, bucket=registry.b3
    )
    if b2_image is None:
        await send_message(
            OutgoingMessage(
                channel=registry.CHANNEL_FORTUNKI,
                thread_ts=None,
                blocks=[Text(f"Niepoprawny obrazek ({plugin}): {url}")],
            )
        )
        return
    elif b2_image.exists:
        logger.warning(f"Image already exists: {b2_image.file_name}.")
        return
    await registry.database.execute(
        query=b2_images.insert(),
        values={
            "plugin": plugin,
            "file_name": b2_image.file_name,
            "hash": b2_image.hash,
            "url": b2_image.url,
        },
    )
    return b2_image.url


@job(60)
async def _upload_from_interim():
    for _ in range(await count(b2_images_interim)):
        async with registry.database.transaction():
            img = await registry.database.fetch_one(
                b2_images_interim.select()
                .where(
                    (b2_images_interim.c.plugin == PLUGIN_NAME_NOSACZE)
                    | (b2_images_interim.c.plugin == PLUGIN_NAME_FEELS)
                )
                .with_for_update(nowait=True)
            )
            if img is None:
                return
            try:
                await _upload_image(img["url"], img["plugin"])
            except Exception:
                await send_message(
                    OutgoingMessage(
                        channel=registry.CHANNEL_FORTUNKI,
                        thread_ts=None,
                        blocks=[
                            Text(
                                f"Nie udało się dodać obrazka "
                                f"({img['plugin']}): {img['url']}"
                            )
                        ],
                    )
                )
            finally:
                await registry.database.execute(
                    b2_images_interim.delete().where(
                        b2_images_interim.c.id == img["id"]
                    )
                )
