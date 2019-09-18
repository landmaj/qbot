import logging

import validators
from bs4 import BeautifulSoup
from sqlalchemy import func

from qbot.core import registry
from qbot.db import nosacze
from qbot.slack.command import add_command
from qbot.slack.message import Image, IncomingMessage, send_reply

logger = logging.getLogger(__name__)


@add_command("nosacz", "halynka dawaj mnie tu te memy", group="nosacze")
async def nosacz(message: IncomingMessage):
    image_url = await registry.database.fetch_val(
        query=nosacze.select().order_by(func.random()), column="url"
    )
    if image_url is None:
        await send_reply(message, text="Nie ma żadnych nosaczy :(")
        return
    await send_reply(message, blocks=[Image(image_url, "nosacz")])


@add_command("nosacz dodaj", "mało ci memów?", group="nosacze")
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
    query = f"INSERT INTO {nosacze.fullname}(url) VALUES (:url) ON CONFLICT DO NOTHING"
    values = [{"url": x} for x in validated]
    await registry.database.execute_many(query, values)
    await send_reply(message, text=f"Nowe nosacze: {len(validated)}.")
    if len(rejected) != 0:
        text = "\n".join(rejected)
        await send_reply(
            message,
            text=f"*Poniższe wartości są niepoprawne i nie zostały dodane:*\n{text}",
        )


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
