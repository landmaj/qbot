from sasin import pln_to_sasin

from qbot.command import add_command
from qbot.message import IncomingMessage, send_reply


@add_command(
    "sasin",
    "Konwersja PLN → sasin. Użycie: `!sasin -- NUMBER`",
    channel="fortunki",
    safe_to_fix=True,
)
async def sasin_command(message: IncomingMessage) -> None:
    if not message.text:
        text = "Użycie: `!sasin -- NUMBER`"
    else:
        try:
            text = pln_to_sasin(float(message.text))
        except ValueError:
            text = "Nie rozumiem, spróbuj czegoś, co przypomina liczbę"
    await send_reply(message, text=text)
