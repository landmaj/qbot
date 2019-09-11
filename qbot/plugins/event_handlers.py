from qbot.slack_utils import event_handler, keyword_to_handler


@event_handler("message")
async def message_handler(event: dict):
    text = event.get("text")
    if text and text.startswith("!") and "bot_id" not in event:
        text = text[1:]
        channel_id = event["channel"]
        for key in sorted(keyword_to_handler.keys(), key=len, reverse=True):
            if text.startswith(key):
                await keyword_to_handler[key](
                    text, channel_id=channel_id, user=event["user"]
                )
                break
