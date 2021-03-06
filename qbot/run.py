import logging
import logging.config
import os
import time

import click
import uvicorn
from starlette.config import environ

import qbot.log
from qbot import cron
from qbot.app import app


def setup_logging():
    logging.config.dictConfig(qbot.log.CONFIG)


HOST = os.environ.get("HOST", "0.0.0.0")
PORT = os.environ.get("PORT", 5000)
environ["DEPLOY_TIMESTAMP"] = str(int(time.time()))


class AppMode:
    SERVER = "server"
    CRON = "cron"


@click.command()
@click.option(f"--{AppMode.SERVER}", "mode", flag_value=AppMode.SERVER)
@click.option(f"--{AppMode.CRON}", "mode", flag_value=AppMode.CRON)
def main(mode):
    setup_logging()

    import qbot.plugins  # noqa

    if mode == AppMode.SERVER:
        uvicorn.run(app, host=HOST, port=int(PORT), log_config=None)
    elif mode == AppMode.CRON:
        cron.run()
    else:
        logging.error("App mode not provided.")


if __name__ == "__main__":
    main()
