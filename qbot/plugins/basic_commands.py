from qbot.registry import registry
from qbot.slack_utils import keyword_to_description, send_message, slack_keyword


@slack_keyword("ping", "dig it!")
async def ping(text: str, channel_id: str, **kwargs) -> None:
    await send_message("Pong!", channel_id)


@slack_keyword("help", "pokaż tę wiadomość")
async def help_message(text: str, channel_id: str, **kwargs) -> None:
    info = (
        f"*Qbot rev. {registry.REVISION}*\n"
        "*Repository:* https://github.com/landmaj/qbot"
    )
    commands = "\n".join(
        [f"*!{key}*: {value}" for key, value in keyword_to_description.items()]
    )
    await send_message("{}\n\n{}".format(info, commands), channel_id)
