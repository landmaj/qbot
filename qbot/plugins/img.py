import logging
from typing import Optional
from urllib.parse import urlparse

from qbot.backblaze import upload_image
from qbot.command import add_command
from qbot.core import registry
from qbot.db import (
    b2_images_interim,
    b2_images_interim_insert,
    b2_images_interim_insert_from_slack,
    count,
)
from qbot.message import (
    IncomingMessage,
    OutgoingMessage,
    Text,
    send_message,
    send_random_image,
    send_reply,
)
from qbot.scheduler import job

logger = logging.getLogger(__name__)
PLUGIN_NAME_NOSACZE = "nosacze"
PLUGIN_NAME_VIRUS = "wirus"
PLUGIN_NAME_PTAK = "ptak"


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
    response = await _add_to_interim(PLUGIN_NAME_NOSACZE, message)
    await send_reply(message, text=response)


@add_command(
    "virus",
    "I tak już masz wirusa.",
    channel="fortunki",
    aliases=["wirus", "korona", "corona", "koronawirus", "coronavirus", "v", "k"],
)
async def virus_cmd(message: IncomingMessage):
    await send_random_image(message, PLUGIN_NAME_VIRUS, "Mem w koronie")


@add_command(
    "virus dodaj",
    "`!virus dodaj -- https://example.com/image.jpg`",
    channel="fortunki",
    safe_to_fix=False,
)
async def virus_dodaj_cmd(message: IncomingMessage):
    response = await _add_to_interim(PLUGIN_NAME_VIRUS, message)
    await send_reply(message, text=response)


@add_command("ptak", "Poka ptaka.", channel="fortunki", aliases=["p", "xxx"])
async def ptak_cmd(message: IncomingMessage):
    await send_random_image(message, PLUGIN_NAME_PTAK, "Ptak Marcina")


@add_command(
    "ptak dodaj",
    "`!ptak dodaj -- https://example.com/image.jpg`",
    channel="fortunki",
    safe_to_fix=False,
)
async def ptak_dodaj_cmd(message: IncomingMessage):
    response = await _add_to_interim(PLUGIN_NAME_PTAK, message)
    await send_reply(message, text=response)


async def _add_to_interim(plugin: str, message: IncomingMessage) -> str:
    if not message.text and not message.files:
        return "Link albo obrazek jest wymagany."
    elif message.text and message.files:
        return "Albo link albo obrazek, nie oba naraz."
    elif message.files:
        return await b2_images_interim_insert_from_slack(plugin, message.files)
    else:
        return await b2_images_interim_insert(plugin, message.text)


async def _upload_image(url: str, plugin: str) -> Optional[str]:
    parsed_url = urlparse(url)
    if parsed_url.netloc == "files.slack.com":
        resp = await registry.http_client.get(
            url,
            headers={"Authorization": f"Bearer {str(registry.SLACK_TOKEN)}"},
            allow_redirects=False,  # to avoid login screen
        )
    else:
        headers = {
            # moodiedavittreport.com returns 403 with default user-agent
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0"
        }
        resp = await registry.http_client.get(url, headers=headers)
    if not 200 <= resp.status_code < 300:
        await send_message(
            OutgoingMessage(
                channel=registry.CHANNEL_FORTUNKI,
                thread_ts=None,
                blocks=[Text(f"Nie udało się pobrać obrazka: {url}")],
            )
        )
        return
    b2_image = await upload_image(
        content=resp.content, plugin=plugin, bucket=registry.b3
    )
    if b2_image is None:
        logger.error(f"Could not determine image extension. Content:\n{resp.content}")
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
    return b2_image.url


@job(60)
async def _upload_from_interim():
    for _ in range(await count(b2_images_interim)):
        async with registry.database.transaction():
            img = await registry.database.fetch_one(
                b2_images_interim.select()
                .where(
                    (b2_images_interim.c.plugin == PLUGIN_NAME_NOSACZE)
                    | (b2_images_interim.c.plugin == PLUGIN_NAME_VIRUS)
                    | (b2_images_interim.c.plugin == PLUGIN_NAME_PTAK)
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
