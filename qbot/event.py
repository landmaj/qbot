from functools import wraps

from qbot.command import ALIASES, COMMANDS, fuzzy_match
from qbot.message import IncomingMessage, send_reply
from qbot.utils import get_channel_name

EVENTS = {}


def add_event(event_type: str):
    """
    Connect Slack event type with a function to handle it.
    """

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            return function(*args, **kwargs)

        EVENTS[event_type] = wrapper
        return wrapper

    return decorator


async def process_slack_event(event: dict, event_id: str):
    await EVENTS[event["type"]](event)


@add_event("message")
async def message_handler(event: dict):
    channel_name = await get_channel_name(event["channel"])
    message = IncomingMessage(
        channel=event["channel"],
        channel_name=channel_name,
        user=event.get("user", "BOT"),
        text=event.get("text", ""),
        ts=event["ts"],
        thread_ts=event.get("thread_ts"),
        files=event.get("files"),
    )
    if message.text.startswith("!") and message.user != "BOT":
        splitted_message = message.text.split("--", 1)
        command = splitted_message[0].lstrip("!").rstrip()
        if len(splitted_message) == 2:
            message.text = splitted_message[1].strip()
        else:
            message.text = ""

        handler = {**COMMANDS, **ALIASES}.get(command)
        if handler:
            await handler(message)
        elif fuzzy_match(command):
            fixed_cmd, ratio = fuzzy_match(command)
            handler = {**COMMANDS, **ALIASES}[fixed_cmd]
            await send_reply(message, text=f"FTFY: {command} -> {fixed_cmd}")
            await handler(message)
        else:
            await send_reply(message, text=f"Nieznane polecenie: {command}")
