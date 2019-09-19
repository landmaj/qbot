from asyncpg import UniqueViolationError

from qbot.core import registry
from qbot.db import fortunki
from qbot.slack.command import add_command
from qbot.slack.message import IncomingMessage, send_reply


@add_command("fortunka", "`!fortunka [-- ID]`", group="fortunki")
async def fortunka_cmd(message: IncomingMessage):
    if message.text:
        try:
            identifier = int(message.text)
        except ValueError:
            await send_reply(message, text="Niepoprawne ID.")
            return
        query = f"SELECT text FROM {fortunki.fullname} WHERE id = :id"
        fortunka = await registry.database.execute(query, {"id": identifier})
        if fortunka is None:
            await send_reply(message, text=f"Nie ma fortunki o ID {identifier}.")
            return
    else:
        query = f"SELECT text FROM {fortunki.fullname} ORDER BY random() LIMIT 1"
        fortunka = await registry.database.execute(query)
        if fortunka is None:
            await send_reply(message, text="Nie ma fortunek :(")
            return
    await send_reply(message, text=fortunka)


@add_command("fortunka dodaj", "`!fortunka dodaj -- TEXT`", group="fortunki")
async def fortunka_dodaj(message: IncomingMessage):
    if not message.text:
        await send_reply(message, text="Pustych fortunek nie dodaję!")
        return
    try:
        async with registry.database.transaction():
            await registry.database.execute(
                query=f"INSERT INTO {fortunki.fullname}(text) VALUES (:text)",
                values={"text": message.text},
            )
    except UniqueViolationError:
        await send_reply(message, text="Taka fortunka już istnieje.")
        return
    identifier = await registry.database.execute(
        query=f"SELECT id from {fortunki.fullname} WHERE text = :text",
        values={"text": message.text},
    )
    await send_reply(message, text=f"Fortunka {identifier} dodana!")
