from qbot.slack.command import add_command
from qbot.slack.message import IncomingMessage, send_reply


@add_command("papuga", "Who the fuck said that!?", aliases=["parrot", "p"])
async def excuse_command(message: IncomingMessage) -> None:
    if message.text:
        await send_reply(message, text=message.text)
    else:
        await send_reply(message, text="Mówiłeś coś?")
