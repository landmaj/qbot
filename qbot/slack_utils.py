from functools import wraps
from urllib.parse import urljoin

from qbot.registry import registry

SLACK_URL = "https://slack.com/api/"

keyword_to_handler = {}
keyword_to_description = {}
event_type_mapping = {}


async def send_slack_message(message: str, channel_id: str) -> None:
    async with registry.http_session.post(
        url=urljoin(SLACK_URL, "chat.postMessage"),
        data={"token": registry.SLACK_TOKEN, "channel": channel_id, "text": message},
    ) as resp:
        pass


def event_handler(event_type: str):
    """
    Connect Slack event type with a function to handle it.
    """

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            return function(*args, **kwargs)

        event_type_mapping[event_type] = wrapper
        return wrapper

    return decorator


def slack_keyword(keyword: str, description: str):
    """
    Add a new !command to be used in chat messages.
    """

    def decorator(function):
        @wraps(function)
        def wrapper(text: str, **kwargs):
            return function(text.replace(keyword, "", 1).lstrip(), **kwargs)

        keyword_to_handler[keyword] = wrapper
        keyword_to_description[keyword] = description
        return wrapper

    return decorator
