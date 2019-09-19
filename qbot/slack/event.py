from functools import wraps

from qbot.slack.command import COMMANDS
from qbot.slack.message import IncomingMessage, send_reply

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
    message = IncomingMessage(
        channel=event["channel"],
        user=event.get("user", "BOT"),
        text=event["text"],
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

        if command in COMMANDS:
            await COMMANDS[command](message)
        else:
            await send_reply(message, text=f"Nieznane polecenie: {command}")
