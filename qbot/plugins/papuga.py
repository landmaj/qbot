import logging
import re

from qbot.command import add_command
from qbot.message import (
    IncomingMessage,
    OutgoingMessage,
    Text,
    send_message,
    send_reply,
)
from qbot.plugins.excuse import bot_malfunction

logger = logging.getLogger(__name__)
CHANNEL_REGEX = re.compile(r"^<#(?P<channel_id>\w*)\|(?P<channel_name>\w*)>\s")


@add_command(
    "papuga",
    "Who the fuck said that!? `!p -- #fortunki message`",
    aliases=["parrot", "p"],
    safe_to_fix=False,
)
async def parrot_command(message: IncomingMessage) -> None:
    if message.text:
        match = CHANNEL_REGEX.search(message.text)
        if match is None:
            await send_reply(
                message, text="SyntaxError: spróbuj `!p -- #fortunki wiadomość`"
            )
            return
        if not await send_message(
            OutgoingMessage(
                channel=match.group("channel_id"),
                thread_ts=None,
                blocks=[Text(message.text[match.end() :])],
            )
        ):
            await bot_malfunction(message)
    else:
        await send_reply(message, text="Mówiłeś coś?")
