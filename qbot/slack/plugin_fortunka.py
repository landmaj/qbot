from asyncpg import UniqueViolationError
from sqlalchemy import func

from qbot.core import registry
from qbot.db import fortunki
from qbot.slack.command import add_command
from qbot.slack.message import IncomingMessage, send_reply
from qbot.utils import add_recently_seen, get_recently_seen


@add_command("fortunka", "`!fortunka [-- ID]`", group="fortunki")
async def fortunka_cmd(message: IncomingMessage):
    if message.text:
        try:
            identifier = int(message.text)
        except ValueError:
            await send_reply(message, text="Niepoprawne ID.")
            return
        result = await registry.database.fetch_one(
            fortunki.select().where(fortunki.c.id == identifier)
        )
        if result is None:
            await send_reply(message, text=f"Nie ma fortunki o ID {identifier}.")
            return
    else:
        recently_seen = await get_recently_seen(fortunki)
        query = fortunki.select()
        if len(recently_seen) != 0:
            query = query.where(fortunki.c.id.notin_(recently_seen))
        query = query.order_by(func.random()).limit(1)
        result = await registry.database.fetch_one(query)
        if result is None:
            await send_reply(message, text="Nie ma fortunek :(")
            return
    await send_reply(message, text=result["text"])
    await add_recently_seen(fortunki, result["id"])


@add_command(
    "fortunka dodaj", "`!fortunka dodaj -- TEXT`", group="fortunki", safe_to_fix=False
)
async def fortunka_dodaj(message: IncomingMessage):
    if not message.text:
        await send_reply(message, text="Pustych fortunek nie dodaję!")
        return
    try:
        async with registry.database.transaction():
            identifier = await registry.database.execute(
                query=fortunki.insert(), values={"text": message.text}
            )
    except UniqueViolationError:
        await send_reply(message, text="Taka fortunka już istnieje.")
        return
    await send_reply(message, text=f"Fortunka {identifier} dodana!")
