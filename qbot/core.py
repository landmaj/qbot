import logging
from datetime import datetime, timedelta
from typing import Optional

import aiohttp
import databases
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
        self.TESTING = config("TESTING", cast=bool, default=False)
        self.DEPLOY_TIMESTAMP = config("DEPLOY_TIMESTAMP", cast=int, default=None)

    async def setup(self):
        self.set_config_vars()
        self.http_session = aiohttp.ClientSession()
        if self.TESTING:
            self.database = databases.Database(
                registry.DATABASE_URL, force_rollback=True
            )
        else:
            self.database = databases.Database(registry.DATABASE_URL)
        await self.database.connect()
        logger.info("Registry setup finished.")

    async def teardown(self):
        await self.http_session.close()
        await self.database.disconnect()

    @property
    def uptime(self) -> Optional[timedelta]:
        if self.DEPLOY_TIMESTAMP is None:
            return
        return datetime.utcnow() - datetime.utcfromtimestamp(self.DEPLOY_TIMESTAMP)


registry = Registry()
