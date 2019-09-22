import logging

import validators
from bs4 import BeautifulSoup
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from qbot.core import registry
from qbot.db import nosacze
from qbot.slack.command import add_command
from qbot.slack.message import Image, IncomingMessage, send_reply
from qbot.utils import add_recently_seen, get_recently_seen

logger = logging.getLogger(__name__)


@add_command("janusz", "losowe memiszcze z janusznosacz.pl", group="nosacze")
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


@add_command("nosacz", "halynka dawaj mnie tu te memy", group="nosacze")
async def nosacz(message: IncomingMessage):
    recently_seen = await get_recently_seen(nosacze)
    query = nosacze.select()
    if len(recently_seen) != 0:
        query = query.where(nosacze.c.id.notin_(recently_seen))
    query = query.order_by(func.random()).limit(1)
    result = await registry.database.fetch_one(query)
    if result is None:
        await send_reply(message, text="Nosacze wyginęły :(")
        return
    await send_reply(message, blocks=[Image(result["url"], "nosacz")])
    await add_recently_seen(nosacze, result["id"])


@add_command(
    "nosacz dodaj",
    "`!nosacz dodaj -- https://example.com/image.jpg`",
    group="nosacze",
    safe_to_fix=False,
)
async def nosacz_dodaj(message: IncomingMessage):
    validated, rejected = [], []
    for line in message.text.split("\n"):
        # for some reason Slack adds triangular brackets to URLs
        line = line.strip("<> ")
        if validators.url(line):
            validated.append(line)
        else:
            rejected.append(line)
    if len(validated) == 0:
        await send_reply(message, text="Nie podałeś żadnych poprawnych URL-i.")
        return
    query = insert(nosacze).on_conflict_do_nothing(index_elements=["url"])
    values = [{"url": x} for x in validated]
    await registry.database.execute_many(query, values)
    await send_reply(message, text=f"Nowe nosacze: {len(validated)}.")
    if len(rejected) != 0:
        text = "\n".join(rejected)
        await send_reply(
            message,
            text=f"*Poniższe wartości są niepoprawne i nie zostały dodane:*\n{text}",
        )
