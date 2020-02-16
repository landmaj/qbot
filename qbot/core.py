from datetime import datetime, timedelta
from typing import Optional

from databases import Database
from httpx import AsyncClient
from starlette.config import Config
from starlette.datastructures import Secret


# noinspection PyAttributeOutsideInit
class Registry:
    http_client: AsyncClient
    database: Database

    def set_config_vars(self):
        config = Config(".env")
        self.REVISION = config("GIT_REV", default="N/A")
        self.SIGNING_SECRET = config("Q_SIGNING_SECRET", cast=Secret)
        self.SLACK_TOKEN = config("Q_SLACK_TOKEN", cast=Secret)
        self.ROOT_DOMAIN = config("Q_ROOT_DOMAIN")
        self.SPAM_CHANNEL_ID = config("Q_SPAM_CHANNEL_ID")
        self.DATABASE_URL = config("DATABASE_URL", cast=Secret)
        self.TESTING = config("TESTING", cast=bool, default=False)
        self.DEPLOY_TIMESTAMP = config("DEPLOY_TIMESTAMP", cast=int, default=None)

    async def setup(self):
        self.set_config_vars()
        self.http_client = AsyncClient()
        if self.TESTING:
            self.database = Database(registry.DATABASE_URL, force_rollback=True)
        else:
            self.database = Database(registry.DATABASE_URL)
        await self.database.connect()

    async def teardown(self):
        await self.http_client.aclose()
        await self.database.disconnect()

    @property
    def uptime(self) -> Optional[timedelta]:
        if self.DEPLOY_TIMESTAMP is None:
            return
        return datetime.utcnow() - datetime.utcfromtimestamp(self.DEPLOY_TIMESTAMP)


registry = Registry()
