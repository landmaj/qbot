import hashlib

from asyncpg import UniqueViolationError

from qbot.app import app
from qbot.command import add_command
from qbot.core import registry
from qbot.db import add_recently_seen, query_with_recently_seen, sucharki
from qbot.message import Image, IncomingMessage, send_reply


@add_command("sucharek", "`!sucharek [-- ID]`", channel="fortunki", aliases=["s"])
async def sucharek_cmd(message: IncomingMessage):
    identifier = None
    if message.text:
        try:
            identifier = int(message.text)
        except ValueError:
            await send_reply(message, text="Niepoprawne ID.")
            return
    result = await query_with_recently_seen(sucharki, identifier)
    if result is None:
        await send_reply(message, text="Źródełko sucharków jest suche.")
        return
    await send_reply(
        message,
        blocks=[
            Image(
                image_url=app.url_path_for("sucharek", sucharek_id=identifier),
                alt_text="Psi Sucharek",
            )
        ],
    )
    await add_recently_seen(sucharki, result["id"])


async def add_sucharek(image: bytes) -> int:
    sha256 = hashlib.sha256()
    sha256.update(image)
    try:
        async with registry.database.transaction():
            return await registry.database.execute(
                query=sucharki.insert(),
                values={"image": image, "digest": sha256.digest()},
            )
    except UniqueViolationError:
        result = await registry.database.fetch_one(
            sucharki.select().where(sucharki.c.digest == sha256.digest())
        )
        return result["id"]
