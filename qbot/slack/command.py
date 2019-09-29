from collections import defaultdict
from functools import lru_cache, wraps
from typing import Optional, Tuple

from fuzzywuzzy import process

from qbot.core import registry
from qbot.db import feels, fortunki, nosacze
from qbot.slack.message import IncomingMessage, send_reply
from qbot.utils import count

COMMANDS = {}
DESCRIPTIONS = defaultdict(lambda: defaultdict())


def add_command(
    keyword: str,
    description: str,
    group: Optional[str] = None,
    safe_to_fix: bool = True,
):
    """
    Add a new !command to be used in chat messages.

    :param keyword: to trigger the command
    :param description: text to show in the help message
    :param group: bundles commands together in the help message, defaults
           to miscellaneous
    :param safe_to_fix: whether command can be automatically called after
           fuzzy matching
    """

    def decorator(function):
        @wraps(function)
        def wrapper(message: IncomingMessage):
            return function(message)

        COMMANDS[keyword] = wrapper
        DESCRIPTIONS[group][keyword] = description
        wrapper.safe_to_fix = safe_to_fix

        return wrapper

    return decorator


@lru_cache()
def fuzzy_match(
    mistyped_command: str, score_cutoff: int = 75
) -> Optional[Tuple[str, int]]:
    match = process.extractBests(
        mistyped_command, COMMANDS.keys(), score_cutoff=score_cutoff, limit=1
    )
    return match[0] if len(match) != 0 else None


@add_command("ping", "dig it!")
async def ping_command(message: IncomingMessage) -> None:
    await send_reply(message, text="Pong!")


@add_command("help", "show this message and exit")
async def help_command(message: IncomingMessage) -> None:
    text = ""
    for group, commands in DESCRIPTIONS.items():
        group = "MISCELLANEOUS" if group is None else group
        group_name = f"*{group.upper()}*"
        group_body = "\n".join(
            [f"*!{key}*: {value}" for key, value in commands.items()]
        )
        text = "\n\n".join([text, "\n".join([group_name, group_body])])
    await send_reply(message, text=text)


@add_command("top", "information about the bot")
async def top_command(message: IncomingMessage):
    uptime = str(registry.uptime).split(".")[0] if registry.uptime else "N/a"
    text = (
        f"*Revision:* {registry.REVISION:.8}\n"
        f"*Uptime:* {uptime}\n"
        f"*Repository:* https://github.com/landmaj/qbot\n"
        f"*Fortunki:* {await count(fortunki)}\n"
        f"*Nosacze:* {await count(nosacze)}\n"
        f"*Smutne nosacze:* {await count(feels)}"
    )
    await send_reply(message, text=text)


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
