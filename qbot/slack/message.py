import abc
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional
from urllib.parse import urljoin

from qbot.core import registry

SLACK_URL = "https://slack.com/api/"
logger = logging.getLogger(__name__)


@lru_cache(maxsize=16)
async def get_channel_id(channel_name: str) -> Optional[str]:
    data = {}
    async with registry.http_session.get(
        url=urljoin(SLACK_URL, "conversations.list"),
        params={"exclude_archived": "true", "types": "public_channel"},
        headers={"Authorization": f"Bearer {str(registry.SLACK_TOKEN)}"},
    ) as resp:
        if not 200 <= resp.status < 400:
            logger.error(f"Incorrect response from Slack. Status: {resp.status}.")
            return
        body = await resp.json()
        if not body["ok"]:
            error = body["error"]
            logger.error(f"Slack returned an error: {error}. Request body: {data}.")
            return None
        name_to_id = {ch["name"]: ch["id"] for ch in body["channels"]}
        return name_to_id.get(channel_name)


async def send_message(message: "OutgoingMessage") -> None:
    data = message.to_dict()
    async with registry.http_session.post(
        url=urljoin(SLACK_URL, "chat.postMessage"),
        json=data,
        headers={"Authorization": f"Bearer {str(registry.SLACK_TOKEN)}"},
    ) as resp:
        if not 200 <= resp.status < 400:
            logger.error(f"Incorrect response from Slack. Status: {resp.status}.")
            return
        body = await resp.json()
        if not body["ok"]:
            error = body["error"]
            logger.error(f"Slack returned an error: {error}. Request body: {data}.")


async def send_reply(
    reply_to: "IncomingMessage",
    text: Optional[str] = None,
    blocks: Optional[List["Block"]] = None,
) -> None:
    if text and blocks:
        raise Exception("Text and blocks cannot be used at the same time.")
    elif text:
        message = OutgoingMessage(
            channel=reply_to.channel, thread_ts=reply_to.thread_ts, blocks=[Text(text)]
        )
    else:
        message = OutgoingMessage(
            channel=reply_to.channel, thread_ts=reply_to.thread_ts, blocks=blocks
        )
    await send_message(message)


@dataclass()
class IncomingMessage:
    channel: str
    user: str
    text: str
    ts: str
    thread_ts: Optional[str]


@dataclass()
class OutgoingMessage:
    channel: str
    thread_ts: Optional[str]
    blocks: [List["Block"]]

    def to_dict(self) -> dict:
        data = {"channel": self.channel}
        # if thread_ts is present, the message will be a reply to a thread
        if self.thread_ts:
            data["thread_ts"] = self.thread_ts
        data["blocks"] = []
        for block in self.blocks:
            data["blocks"].append(block.to_dict())
        return data


class Block(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def to_dict(self) -> dict:
        pass


@dataclass()
class Text(Block):
    text: str

    def to_dict(self) -> dict:
        return {"type": "section", "text": {"type": "mrkdwn", "text": self.text}}


@dataclass()
class Image(Block):
    image_url: str
    alt_text: str

    def to_dict(self) -> dict:
        return {"type": "image", "image_url": self.image_url, "alt_text": self.alt_text}


@dataclass()
class TextWithButton(Block):
    text: str
    button_text: str

    def to_dict(self) -> dict:
        return {
            "type": "section",
            "text": {"type": "mrkdwn", "text": self.text},
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": self.button_text},
            },
        }
