import logging

from qbot.slack.command import add_command
from qbot.slack.message import (
    IncomingMessage,
    OutgoingMessage,
    Text,
    get_channel_id,
    send_message,
    send_reply,
)

logger = logging.getLogger(__name__)


@add_command("papuga", "Who the fuck said that!?", aliases=["parrot", "p"])
async def excuse_command(message: IncomingMessage) -> None:
    if message.text:
        splitted_message = message.text.split(" ", 1)
        logger.error(message.text)
        if not splitted_message[0].startswith("#"):
            await send_reply(message, text="Nazwa kanału powinna zaczynać się `#`.")
            return
        elif len(splitted_message) != 2:
            await send_reply(
                message, text="SyntaxError: spróbuj !papuga -- #channel message"
            )
            return
        channel_id = await get_channel_id(splitted_message[0].lstrip("#").rstrip())
        if channel_id is None:
            await send_reply(message, text="Na pewno poprawna nazwa kanału?")
            return
        await send_message(
            OutgoingMessage(
                channel=channel_id, thread_ts=None, blocks=[Text(splitted_message[1])]
            )
        )
        await send_reply(message, text=message.text)
    else:
        await send_reply(message, text="Mówiłeś coś?")
