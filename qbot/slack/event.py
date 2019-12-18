import logging
from functools import wraps

from qbot.slack.command import COMMANDS, fuzzy_match
from qbot.slack.message import IncomingMessage, send_reply

EVENTS = {}

logger = logging.getLogger(__name__)


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
    message = IncomingMessage(
        channel=event["channel"],
        user=event.get("user", "BOT"),
        text=event.get("text", ""),
        ts=event["ts"],
        thread_ts=event.get("thread_ts"),
    )
    if message.text.startswith("!") and message.user != "BOT":
        splitted_message = message.text.split("--", 1)
        command = splitted_message[0].lstrip("!").rstrip()
        if len(splitted_message) == 2:
            message.text = splitted_message[1].strip()
        else:
            message.text = ""

        logger.info(
            f"Command received. Message: {message}.",
            extra={"command": command, "user": message.user},
        )

        if command in COMMANDS:
            await COMMANDS[command](message)
        elif fuzzy_match(command):
            fixed_cmd, ratio = fuzzy_match(command)
            handler = COMMANDS[fixed_cmd]
            if handler.safe_to_fix:
                await send_reply(message, text=f"FTFY: {command} -> {fixed_cmd}")
                await handler(message)
            else:
                await send_reply(
                    message,
                    text=f"Jestem w {ratio}% pewien, że chodziło o `{fixed_cmd}`.",
                )
        else:
            await send_reply(message, text=f"Nieznane polecenie: {command}")
