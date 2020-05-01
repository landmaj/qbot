from random import random

from qbot.command import DESCRIPTIONS, add_command
from qbot.core import registry
from qbot.db import b2_images_count, count, fortunki
from qbot.message import IncomingMessage, send_reply
from qbot.plugins.img import PLUGIN_NAME_NOSACZE as NOSACZE
from qbot.plugins.img import PLUGIN_NAME_VIRUS as VIRUS
from qbot.plugins.sucharki import PLUGIN_NAME as SUCHARKI


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


@add_command("about", "podstawowe informacje o bocie")
async def about_command(message: IncomingMessage):
    text = (
        f"*Qbot rev.* {registry.REVISION:.8}\n"
        f"*Repository:* https://github.com/landmaj/qbot\n"
        f"*Contributors*:\n"
        f'\t- Michał "landmaj" Wieluński\n'
        f'\t- Adrian "Necior" Sadłocha'
    )
    await send_reply(message, text=text)


@add_command("top", "statystyki bota")
async def top_command(message: IncomingMessage):
    text = (
        f"*Fortunki:* {await count(fortunki)}\n"
        f"*Nosacze:* {await b2_images_count(NOSACZE)}\n"
        f"*Psie sucharki:* {await b2_images_count(SUCHARKI)}\n"
        f"*Wirusy:* {await b2_images_count(VIRUS)}"
    )
    await send_reply(message, text=text)


@add_command("uptime", "czas od ostatniego restartu")
async def uptime_command(message: IncomingMessage) -> None:
    if registry.uptime is None:
        await send_reply(message, text="N/A")
        return
    uptime = str(registry.uptime).split(".")[0] if registry.uptime else "N/a"
    await send_reply(message, text=f"Uptime: {uptime}")
