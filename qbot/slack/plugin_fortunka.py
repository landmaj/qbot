from asyncpg import UniqueViolationError

from qbot.core import registry
from qbot.db import fortunki
from qbot.slack.command import add_command
from qbot.slack.db_utils import query_with_recently_seen
from qbot.slack.message import IncomingMessage, TextWithButton, send_reply
from qbot.utils import add_recently_seen


@add_command("fortunka", "`!fortunka [-- ID]`", group="fortunki")
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
        return send_reply(message, text="O cokolwiek prosiłeś - nie istnieje.")
    await send_reply(
        message,
        blocks=[TextWithButton(text=result["text"], button_text=str(result["id"]))],
    )
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
