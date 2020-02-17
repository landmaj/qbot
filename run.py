import logging
import logging.config
import os
import time

import click
import uvicorn
from starlette.config import environ

import qbot.logging
from qbot import scheduler
from qbot.app import app


def setup_logging():
    logging.config.dictConfig(qbot.logging.CONFIG)


HOST = os.environ.get("Q_HOST", "0.0.0.0")
PORT = os.environ.get("Q_PORT", 5000)
environ["DEPLOY_TIMESTAMP"] = str(int(time.time()))


class AppMode:
    SCHEDULER = "scheduler"
    SERVER = "server"


@click.command()
@click.option(f"--{AppMode.SERVER}", "mode", flag_value=AppMode.SERVER)
@click.option(f"--{AppMode.SCHEDULER}", "mode", flag_value=AppMode.SCHEDULER)
def main(mode):
    setup_logging()

    logging.info(f"Application startup mode: {mode}.")
    import qbot.plugins  # noqa

    if mode == AppMode.SERVER:
        uvicorn.run(app, host=HOST, port=int(PORT))
    elif mode == AppMode.SCHEDULER:
        scheduler.run()
    else:
        logging.error("App mode not provided.")


if __name__ == "__main__":
    main()
