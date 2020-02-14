from collections import defaultdict
from functools import lru_cache, wraps
from typing import Optional, Tuple

from fuzzywuzzy import process

from qbot.message import IncomingMessage

COMMANDS = {}
ALIASES = {}
DESCRIPTIONS = defaultdict(lambda: defaultdict())


def add_command(
    keyword: str,
    description: str,
    group: Optional[str] = None,
    safe_to_fix: bool = True,
    aliases: list = [],
):
    """
    Add a new !command to be used in chat messages.

    :param keyword: to trigger the command
    :param description: text to show in the help message
    :param group: bundles commands together in the help message, defaults
           to miscellaneous
    :param safe_to_fix: whether command can be automatically called after
           fuzzy matching
    :param aliases: additional keywords, not listed in the help message
    """

    def decorator(function):
        @wraps(function)
        def wrapper(message: IncomingMessage):
            return function(message)

        COMMANDS[keyword] = wrapper
        for alias in aliases:
            ALIASES[alias] = wrapper
        DESCRIPTIONS[group][keyword] = description
        wrapper.safe_to_fix = safe_to_fix

        return wrapper

    return decorator


@lru_cache()
def fuzzy_match(
    mistyped_command: str, score_cutoff: int = 75
) -> Optional[Tuple[str, int]]:
    match = process.extractBests(
        mistyped_command, COMMANDS.keys(), score_cutoff=score_cutoff, limit=1
    )
    if len(match) == 0:
        match = process.extractBests(
            mistyped_command, ALIASES.keys(), score_cutoff=score_cutoff, limit=1
        )
    return match[0] if len(match) != 0 else None
