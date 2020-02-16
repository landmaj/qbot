from random import random

from qbot.command import DESCRIPTIONS, add_command
from qbot.core import registry
from qbot.db import count, fortunki, nosacze, sucharki
from qbot.message import IncomingMessage, send_reply


@add_command("ping", "dig it!")
async def ping_command(message: IncomingMessage) -> None:
    if random() <= 0.1:
        await send_reply(message, text=":ok_hand:")
    else:
        await send_reply(message, text="Pong!")


@add_command("help", "pokaż tę wiadomość i wyjdź", aliases=["pomoc"])
async def help_command(message: IncomingMessage) -> None:
    text = ""
    for group, commands in DESCRIPTIONS.items():
        group = "RÓŻNOŚCI" if group is None else group
        group_name = f"*{group.upper()}*"
        group_body = "\n".join(
            [f"*!{key}*: {value}" for key, value in commands.items()]
        )
        text = "\n\n".join([text, "\n".join([group_name, group_body])])
    await send_reply(message, text=text)


@add_command("top", "statystyki bota")
async def top_command(message: IncomingMessage):
    uptime = str(registry.uptime).split(".")[0] if registry.uptime else "N/a"
    text = (
        f"*Revision:* {registry.REVISION:.8}\n"
        f"*Uptime:* {uptime}\n"
        f"*Repository:* https://github.com/landmaj/qbot\n"
        f"*Fortunki:* {await count(fortunki)}\n"
        f"*Nosacze:* {await count(nosacze)}\n"
        f"*Psie sucharki:* {await count(sucharki)}"
    )
    await send_reply(message, text=text)


@add_command("uptime", "czas od ostatniego restartu")
async def uptime_command(message: IncomingMessage) -> None:
    if registry.uptime is None:
        await send_reply(message, text="N/A")
        return
    total_seconds = int(registry.uptime.total_seconds())
    days = total_seconds // 86_400
    hours = total_seconds % 86_400 // 3600
    minutes = total_seconds % 3600 // 60
    seconds = total_seconds % 60
    if days:
        text = f"*Uptime:* {days} dni {hours} godzin {minutes} minut i {seconds} sekund"
    elif hours:
        text = f"*Uptime:* {hours} godzin {minutes} minut i {seconds} sekund"
    elif minutes:
        text = f"*Uptime:* {minutes} minut i {seconds} sekund"
    else:
        text = f"*Uptime:* {seconds} sekund"
    await send_reply(message, text=text)
