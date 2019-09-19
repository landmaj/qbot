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


@add_command("help", "show this message and exit")
async def help_message(message: IncomingMessage) -> None:
    uptime = str(registry.uptime).split(".")[0] if registry.uptime else "N/a"
    header = (
        f"*Qbot rev. {registry.REVISION:.8}*\n"
        "*Repository:* https://github.com/landmaj/qbot\n"
        f"*Uptime:* {uptime}"
    )
    body = ""
    for group, commands in DESCRIPTIONS.items():
        group = "MISCELLANEOUS" if group is None else group
        group_name = f"\n*{group.upper()}*"
        group_body = "\n".join(
            [f"*!{key}*: {value}" for key, value in commands.items()]
        )
        body = "\n".join([body, group_name, group_body])
    await send_reply(message, text=f"{header}\n{body}")


@add_command("uptime", "time since last restart")
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
        text = f"*Uptime:* {days} days {hours} hours {minutes} minutes and {seconds} seconds"
    elif hours:
        text = f"*Uptime:* {hours} hours {minutes} minutes and {seconds} seconds"
    elif minutes:
        text = f"*Uptime:* {minutes} minutes and {seconds} seconds"
    else:
        text = f"*Uptime:* {seconds} seconds"
    await send_reply(message, text=text)
