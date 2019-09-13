import logging
from typing import Optional

from bs4 import BeautifulSoup

from qbot.registry import registry
from qbot.slack_utils import send_image, send_message, slack_keyword

logger = logging.getLogger(__name__)


@slack_keyword("nosacz", "losowe memiszcze")
async def nosacz(text: str, channel_id: str, parent_id: Optional[str], **kwargs):
    while True:
        async with registry.http_session.get(
            "http://www.janusznosacz.pl/losuj"
        ) as resp:
            if not 200 <= resp.status < 400:
                logging.error(
                    f"Incorrect response from janusznosacz.pl. Status: {resp.status}."
                )
                await send_message("Oops, bot spadł z rowerka...", channel_id)
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
        await send_message("Źródełko wyschło. :(", channel_id)
        return
    await send_image(image_url, alt_text, channel_id, parent_id)
