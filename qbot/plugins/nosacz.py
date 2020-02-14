import logging

from bs4 import BeautifulSoup

from qbot.command import add_command
from qbot.core import registry
from qbot.db import add_recently_seen, add_urls, nosacze, query_with_recently_seen
from qbot.message import Image, IncomingMessage, send_reply
from qbot.plugins.excuse import bot_malfunction

logger = logging.getLogger(__name__)


@add_command(
    "janusz",
    "losowe memiszcze z janusznosacz.pl",
    channel="fortunki",
    aliases=["j", "janush"],
)
async def janusz(message: IncomingMessage):
    while True:
        async with registry.http_session.get(
            "http://www.janusznosacz.pl/losuj"
        ) as resp:
            if not 200 <= resp.status < 400:
                logger.error(
                    f"Incorrect response from janusznosacz.pl. Status: {resp.status}."
                )
                await bot_malfunction(message)
                return
            # random image sometimes returns an error and redirects to the home page
            if resp.url.path == "/":
                continue
            body = await resp.text()
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


@add_command("nosacz", "`!nosacz [-- ID]`", channel="fortunki", aliases=["n", "no"])
async def nosacz(message: IncomingMessage):
    identifier = None
    if message.text:
        try:
            identifier = int(message.text)
        except ValueError:
            await send_reply(message, text="Niepoprawne ID.")
            return
    result = await query_with_recently_seen(nosacze, identifier)
    if result is None:
        await send_reply(message, text="Nosaczy jak lodu, ale takiego nie ma.")
        return
    await send_reply(message, blocks=[Image(result["url"], "nosacz")])
    await add_recently_seen(nosacze, result["id"])


@add_command(
    "nosacz dodaj",
    "`!nosacz dodaj -- https://example.com/image.jpg`",
    channel="fortunki",
    safe_to_fix=False,
)
async def nosacz_dodaj(message: IncomingMessage):
    text = await add_urls(nosacze, message.text)
    await send_reply(message, text=text)
