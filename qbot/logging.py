import logging
import sys
from typing import Optional

import click

LINE_SEPARATOR = "\u000d\u000b"

CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"default": {"()": "qbot.logging.LokiFormatter"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "level": "INFO",
            "formatter": "default",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}


class LokiFormatter(logging.Formatter):
    """
    A custom log formatter class that outputs the LOG_LEVEL with an appropriate color.
    """

    level_name_colors = {
        logging.DEBUG: lambda level_name: click.style(str(level_name), fg="cyan"),
        logging.INFO: lambda level_name: click.style(str(level_name), fg="green"),
        logging.WARNING: lambda level_name: click.style(str(level_name), fg="yellow"),
        logging.ERROR: lambda level_name: click.style(str(level_name), fg="red"),
        logging.CRITICAL: lambda level_name: click.style(
            str(level_name), fg="bright_red"
        ),
    }

    def __init__(
        self,
        fmt: Optional[str] = "%(levelname)s %(name)s %(message)s",
        datefmt: Optional[str] = None,
        style: str = "%",
    ) -> None:
        self.real_terminal = sys.stdout.isatty()
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def color_level_name(self, level_name: str, level_no: int) -> str:
        if self.real_terminal:
            default = lambda level_name: str(level_name)
            func = self.level_name_colors.get(level_no, default)
            return func(level_name)
        return level_name

    def color_label(self, text: str) -> str:
        if self.real_terminal:
            return click.style(text, fg="bright_black")
        return text

    def formatMessage(self, record: logging.LogRecord) -> str:
        level_name = self.color_level_name(record.levelname, record.levelno)
        separator = " " * (8 - len(record.levelname))
        record.__dict__["levelname"] = level_name + ": " + separator

        logger = record.name
        record.__dict__["name"] = f"{self.color_label('logger=' + logger)}"

        return super().formatMessage(record)

    def format(self, record: logging.LogRecord):
        log = super().format(record)
        if self.real_terminal:
            return log
        return log.replace("\r\n", LINE_SEPARATOR).replace("\n", LINE_SEPARATOR)
