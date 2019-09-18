import logging

from bs4 import BeautifulSoup

from qbot.core import registry
from qbot.slack.command import add_command
from qbot.slack.message import Image, IncomingMessage, send_reply

logger = logging.getLogger(__name__)


@add_command("janusz", "losowe memiszcze", group="nosacze")
async def janusz(message: IncomingMessage):
    while True:
        async with registry.http_session.get(
            "http://www.janusznosacz.pl/losuj"
        ) as resp:
            if not 200 <= resp.status < 400:
                logging.error(
                    f"Incorrect response from janusznosacz.pl. Status: {resp.status}."
                )
                await send_reply(message, "Oops, bot spadł z rowerka...")
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
        await send_reply(message, "Źródełko wyschło. :(")
        return
    await send_reply(message, blocks=[Image(image_url, alt_text)])
