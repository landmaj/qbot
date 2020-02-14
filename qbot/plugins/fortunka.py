from asyncpg import UniqueViolationError

from qbot.command import add_command
from qbot.core import registry
from qbot.db import add_recently_seen, fortunki, query_with_recently_seen
from qbot.message import IncomingMessage, TextWithButton, send_reply


@add_command("fortunka", "`!fortunka [-- ID]`", group="spam", aliases=["f", "funia"])
async def fortunka_cmd(message: IncomingMessage):
    identifier = None
    if message.text:
        try:
            identifier = int(message.text)
        except ValueError:
            await send_reply(message, text="Niepoprawne ID.")
            return
    result = await query_with_recently_seen(fortunki, identifier)
    if result is None:
        await send_reply(
            message, text="Do 2137 fortunek jeszcze trochę. Tej o którą prosisz nie ma."
        )
        return
    await send_reply(
        message,
        blocks=[TextWithButton(text=result["text"], button_text=str(result["id"]))],
    )
    await add_recently_seen(fortunki, result["id"])


@add_command(
    "fortunka dodaj", "`!fortunka dodaj -- TEXT`", group="spam", safe_to_fix=False
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
        await send_reply(message, text="Drugi raz nie dodaję!")
        return
    await send_reply(message, text=f"Fortunka {identifier} dodana!")
