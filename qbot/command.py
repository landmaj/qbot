from collections import defaultdict
from functools import lru_cache, wraps
from typing import List, Optional, Tuple

from fuzzywuzzy import process

from qbot.message import IncomingMessage, send_reply

COMMANDS = {}
ALIASES = {}
DESCRIPTIONS = defaultdict(lambda: defaultdict())
FUZZY_COMMANDS = {}
FUZZY_ALIASES = {}


def add_command(
    keyword: str,
    description: str,
    channel: Optional[str] = None,
    safe_to_fix: bool = True,
    aliases: Optional[List[str]] = None,
):
    """
    Add a new !command to be used in chat messages.

    :param keyword: to trigger the command
    :param description: text to show in the help message
    :param channel: bundles commands together in the help message, defaults
           to miscellaneous
    :param safe_to_fix: whether command can be automatically called after
           fuzzy matching
    :param aliases: additional keywords, not listed in the help message
    """

    if aliases is None:
        aliases = []

    def decorator(function):
        @wraps(function)
        def wrapper(message: IncomingMessage):
            if (
                wrapper.channel
                and message.channel_name
                and message.channel_name != "im"
                and wrapper.channel != message.channel_name
            ):
                return send_reply(message, text="Niewłaściwy kanał.")
            return function(message)

        wrapper.channel = channel
        COMMANDS[keyword] = wrapper
        if safe_to_fix:
            FUZZY_COMMANDS[keyword] = wrapper
        for alias in aliases:
            ALIASES[alias] = wrapper
            if safe_to_fix:
                FUZZY_ALIASES[alias] = wrapper
        DESCRIPTIONS[channel][keyword] = description

        return wrapper

    return decorator


@lru_cache()
def fuzzy_match(
    mistyped_command: str, score_cutoff: int = 75
) -> Optional[Tuple[str, int]]:
    match = process.extractBests(
        mistyped_command, FUZZY_COMMANDS.keys(), score_cutoff=score_cutoff, limit=1
    )
    if len(match) == 0:
        match = process.extractBests(
            mistyped_command, FUZZY_ALIASES.keys(), score_cutoff=score_cutoff, limit=1
        )
    return match[0] if len(match) != 0 else None
