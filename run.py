import logging
import os
import time

import sentry_sdk
import uvicorn
from httpx import BasicAuth
from ploki import Ploki
from starlette.config import environ

from qbot.app import app


def setup_logging():
    revision = os.environ.get("GIT_REV", "N/A")

    def add_app_details(event, log):
        event["stream"]["application"] = "qbot"
        event["stream"]["revision"] = revision
        return event

    sentry_dsn = os.environ.get("Q_SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(dsn=sentry_dsn, release=revision)

    loki_url = os.environ.get("LOKI_URL", "localhost:3100")
    loki_user = os.environ.get("LOKI_USER", "")
    loki_pass = os.environ.get("LOKI_PASSWORD", "")

    Ploki().initialize(
        url=loki_url,
        auth=BasicAuth(loki_user, loki_pass),
        level=logging.INFO,
        processors=(add_app_details,),
    )
    logging.info("Logging setup finished.")


setup_logging()

HOST = os.environ.get("Q_HOST", "0.0.0.0")
PORT = os.environ.get("Q_PORT", 5000)
environ["DEPLOY_TIMESTAMP"] = str(int(time.time()))

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=int(PORT))
