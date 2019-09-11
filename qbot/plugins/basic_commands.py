from qbot.registry import registry
from qbot.slack_utils import keyword_to_description, slack_keyword


@slack_keyword("ping", "dig it!")
def ping(text: str, **kwargs) -> str:
    return "Pong!"


@slack_keyword("help", "pokaż tę wiadomość")
def help_message(text: str, **kwargs) -> str:
    info = (
        f"*Qbot rev. {registry.REVISION}*\n"
        "*Repository:* https://github.com/landmaj/qbot"
    )
    commands = "\n".join(
        [f"*!{key}*: {value}" for key, value in keyword_to_description.items()]
    )
    return "{}\n\n{}".format(info, commands)
