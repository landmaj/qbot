import abc
import logging
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin

from pydantic.dataclasses import dataclass as pydantic_dataclass
from pydantic.networks import AnyHttpUrl
from sqlalchemy import func

from qbot.consts import SLACK_URL
from qbot.core import registry
from qbot.db import b2_images

logger = logging.getLogger(__name__)


async def send_message(message: "Message") -> bool:
    data = message.to_dict()
    resp = await registry.http_client.post(
        url=urljoin(SLACK_URL, "chat.postMessage"),
        json=data,
        headers={"Authorization": f"Bearer {str(registry.SLACK_TOKEN)}"},
    )
    if not 200 <= resp.status_code < 400:
        logger.error(f"Incorrect response from Slack. Status: {resp.status}.")
        return False
    body = resp.json()
    if not body["ok"]:
        error = body["error"]
        logger.error(f"Slack returned an error: {error}. Request body: {data}.")
        return False
    return True


async def send_reply(
    reply_to: "IncomingMessage",
    text: Optional[str] = None,
    blocks: Optional[List["Block"]] = None,
) -> bool:
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
    return await send_message(message)


async def send_random_image(
    message: "IncomingMessage", plugin_name: str, alt_text: str
) -> None:
    result = await registry.database.fetch_one(
        b2_images.select()
        .order_by(func.random())
        .where((b2_images.c.plugin == plugin_name) & (b2_images.c.deleted == False))
    )
    if result is None:
        await send_reply(message, text="Ni mo!")
        return
    await send_reply(
        message, blocks=[Image(image_url=result["url"], alt_text=alt_text)]
    )


@dataclass()
class IncomingMessage:
    channel: str
    channel_name: Optional[str]
    user: str
    text: str
    ts: str
    thread_ts: Optional[str]
    files: Optional[List[dict]]


@dataclass()
class Message:
    def to_dict(self) -> dict:
        raise NotImplementedError


@dataclass()
class SimpleMessage(Message):
    channel: str
    text: str

    def to_dict(self) -> dict:
        return {"channel": self.channel, "text": self.text}


@dataclass()
class OutgoingMessage(Message):
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


@pydantic_dataclass()
class TextWithLink(Block):
    text: str
    link: AnyHttpUrl

    def to_dict(self) -> dict:
        return {
            "type": "section",
            "text": {"type": "mrkdwn", "text": self.text},
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "GO"},
                "url": self.link,
            },
        }
