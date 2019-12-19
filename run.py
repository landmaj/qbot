import logging
import os
import time

import sentry_sdk
import uvicorn
from ploki import Ploki
from starlette.config import environ

from qbot.app import app


def setup_logging():
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("loki").setLevel(logging.CRITICAL)
    revision = os.environ.get("GIT_REV", "N/A")

    sentry_dsn = os.environ.get("Q_SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(dsn=sentry_dsn, release=revision)

    loki_url = os.environ.get("LOKI_URL", "http://localhost:3100")
    loki_user = os.environ.get("LOKI_USER", "")
    loki_pass = os.environ.get("LOKI_PASSWORD", "")

    Ploki().initialize(
        url=loki_url,
        tags={"application": "qbot", "revision": revision},
        auth=(loki_user, loki_pass),
        level=logging.INFO,
    )
    logging.info("Logging setup finished.")


setup_logging()

HOST = os.environ.get("Q_HOST", "0.0.0.0")
PORT = os.environ.get("Q_PORT", 5000)
environ["DEPLOY_TIMESTAMP"] = str(int(time.time()))

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=int(PORT))
