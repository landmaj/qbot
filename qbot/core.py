import logging
from datetime import datetime, timedelta
from typing import Optional

import aiohttp
import databases
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.applications import Starlette
from starlette.config import Config
from starlette.datastructures import Secret

logger = logging.getLogger(__name__)

# noinspection PyAttributeOutsideInit
class Registry:
    def set_config_vars(self):
        config = Config(".env")
        self.REVISION = config("GIT_REV", default="N/A")
        self.SIGNING_SECRET = config("Q_SIGNING_SECRET", cast=Secret)
        self.SLACK_TOKEN = config("Q_SLACK_TOKEN", cast=Secret)
        self.DATABASE_URL = config("DATABASE_URL", cast=Secret)
        self.SENTRY_DSN = config("Q_SENTRY_DSN", cast=Secret, default=None)
        self.TESTING = config("TESTING", cast=bool, default=False)
        self.DEPLOY_TIMESTAMP = config("DEPLOY_TIMESTAMP", cast=int, default=None)

    async def setup(self, starlette: Starlette = None):
        self.set_config_vars()

        if self.SENTRY_DSN:
            sentry_sdk.init(dsn=str(self.SENTRY_DSN), release=self.REVISION)
        else:
            logger.warning("Sentry integration is disabled.")
        if self.SENTRY_DSN and starlette:
            starlette.add_middleware(SentryAsgiMiddleware)

        self.http_session = aiohttp.ClientSession()

        if self.TESTING:
            self.database = databases.Database(
                registry.DATABASE_URL, force_rollback=True
            )
        else:
            self.database = databases.Database(registry.DATABASE_URL)
        await self.database.connect()

    async def teardown(self):
        await self.http_session.close()
        await self.database.disconnect()

    @property
    def uptime(self) -> Optional[timedelta]:
        if self.DEPLOY_TIMESTAMP is None:
            return
        return datetime.utcnow() - datetime.utcfromtimestamp(self.DEPLOY_TIMESTAMP)


registry = Registry()
