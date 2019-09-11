from qbot.registry import registry
from qbot.slack_utils import keyword_to_description, send_slack_message, slack_keyword


@slack_keyword("ping", "dig it!")
def ping(text: str, channel_id: str, **kwargs) -> None:
    send_slack_message("Pong!", channel_id)


@slack_keyword("help", "pokaż tę wiadomość")
def help_message(text: str, channel_id: str, **kwargs) -> None:
    info = (
        f"*Qbot rev. {registry.REVISION}*\n"
        "*Repository:* https://github.com/landmaj/qbot"
    )
    commands = "\n".join(
        [f"*!{key}*: {value}" for key, value in keyword_to_description.items()]
    )
    send_slack_message("{}\n\n{}".format(info, commands), channel_id)
