import logging
from functools import wraps
from typing import Optional
from urllib.parse import urljoin

from qbot.registry import registry

SLACK_URL = "https://slack.com/api/"

keyword_to_handler = {}
keyword_to_description = {}
event_type_mapping = {}


logger = logging.getLogger(__name__)


async def send_message(
    message: str, channel_id: str, parent_id: Optional[str] = None
) -> None:
    data = {"channel": channel_id, "text": message}
    if parent_id:
        data["thread_ts"] = parent_id
    async with registry.http_session.post(
        url=urljoin(SLACK_URL, "chat.postMessage"),
        json=data,
        headers={"Authorization": f"Bearer {registry.SLACK_TOKEN}"},
    ) as resp:
        if not 200 <= resp.status < 400:
            logger.error(f"Incorrect response from Slack. Status: {resp.status}.")
            return
        body = await resp.json()
        if not body["ok"]:
            error = body["error"]
            logger.error(f"Slack returned an error: {error}. Request body: {data}.")


async def send_image(
    image_url: str, alt_text: str, channel_id: str, parent_id: Optional[str] = None
) -> None:
    data = {
        "channel": channel_id,
        "blocks": [{"type": "image", "image_url": image_url, "alt_text": alt_text}],
    }
    if parent_id:
        data["thread_ts"] = parent_id
    async with registry.http_session.post(
        url=urljoin(SLACK_URL, "chat.postMessage"),
        json=data,
        headers={"Authorization": f"Bearer {registry.SLACK_TOKEN}"},
    ) as resp:
        if not 200 <= resp.status < 400:
            logger.error(f"Incorrect response from Slack. Status: {resp.status}.")
            return
        body = await resp.json()
        if not body["ok"]:
            error = body["error"]
            logger.error(f"Slack returned an error: {error}. Request body: {data}.")


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
        def wrapper(text: str, *args, **kwargs):
            return function(text.replace(keyword, "", 1).lstrip(), *args, **kwargs)

        keyword_to_handler[keyword] = wrapper
        keyword_to_description[keyword] = description
        return wrapper

    return decorator
