import logging

from bs4 import BeautifulSoup

from qbot.command import add_command
from qbot.core import registry
from qbot.message import Image, IncomingMessage, send_reply
from qbot.plugins.excuse import bot_malfunction

logger = logging.getLogger(__name__)


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
