import abc
import logging
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin

from qbot.registry import registry

SLACK_URL = "https://slack.com/api/"
logger = logging.getLogger(__name__)


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
    message = OutgoingMessage(
        channel=reply_to.channel, thread_ts=reply_to.thread_ts, text=text, blocks=blocks
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
    text: Optional[str]
    blocks: Optional[List["Block"]]

    def to_dict(self) -> dict:
        data = {"channel": self.channel}
        # if thread_ts is present, the message will be a reply to a thread
        if self.thread_ts:
            data["thread_ts"] = self.thread_ts
        if self.text:
            data["text"] = self.text
        if self.blocks:
            data["blocks"] = []
            for block in self.blocks:
                data["blocks"].append(block.to_dict())
        return data


class Block(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def to_dict(self) -> dict:
        pass


@dataclass()
class Image(Block):
    image_url: str
    alt_text: str

    def to_dict(self) -> dict:
        return {"type": "image", "image_url": self.image_url, "alt_text": self.alt_text}
