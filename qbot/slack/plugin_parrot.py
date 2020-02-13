from qbot.slack.command import add_command
from qbot.slack.message import IncomingMessage, delete_message, send_reply


@add_command("papuga", "Who the fuck said that!?", aliases=["parrot", "p"])
async def excuse_command(message: IncomingMessage) -> None:
    await delete_message(message)
    await send_reply(message, text=message.text)
