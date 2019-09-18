from collections import defaultdict
from functools import wraps
from typing import Optional

from qbot.core import registry
from qbot.slack.message import IncomingMessage, send_reply

COMMANDS = {}
DESCRIPTIONS = defaultdict(lambda: defaultdict())


def add_command(keyword: str, description: str, group: Optional["str"] = None):
    """
    Add a new !command to be used in chat messages.
    """

    def decorator(function):
        @wraps(function)
        def wrapper(message: IncomingMessage):
            return function(message)

        COMMANDS[keyword] = wrapper
        DESCRIPTIONS[group][keyword] = description

        return wrapper

    return decorator


@add_command("ping", "dig it!")
async def ping(message: IncomingMessage) -> None:
    await send_reply(message, text="Pong!")


@add_command("help", "pokaż tę wiadomość")
async def help_message(message: IncomingMessage) -> None:
    header = (
        f"*Qbot rev. {registry.REVISION:.8}*\n"
        "*Repository:* https://github.com/landmaj/qbot"
    )
    body = ""
    for group, commands in DESCRIPTIONS.items():
        group = "MISCELLANEOUS" if group is None else group
        group_name = f"\n*{group.upper()}*"
        group_body = "\n".join(
            [f"*!{key}*: {value}" for key, value in commands.items()]
        )
        body = "\n".join([body, group_name, group_body])
    await send_reply(message, text=f"{header}\n\n{body}")
