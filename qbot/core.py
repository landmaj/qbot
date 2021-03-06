from datetime import datetime, timedelta
from typing import Optional

from b2sdk.bucket import Bucket
from databases import Database
from httpx import AsyncClient
from starlette.config import Config
from starlette.datastructures import Secret


# noinspection PyAttributeOutsideInit
class Registry:
    http_client: AsyncClient
    database: Database
    _b3: Bucket = None

    def set_config_vars(self):
        self.config = Config(".env")

        self.REVISION = self.config("GIT_REV", default="N/A")
        self.DEPLOY_TIMESTAMP = self.config("DEPLOY_TIMESTAMP", cast=int, default=None)

        self.SLACK_SIGNING_SECRET = self.config("SLACK_SIGNING_SECRET", cast=Secret)
        self.SLACK_TOKEN = self.config("SLACK_TOKEN", cast=Secret)

        self.DATABASE_URL = self.config("DATABASE_URL", cast=Secret, default=None)
        if self.DATABASE_URL is None:
            user = self.config("PG_USER", default="postgres")
            password = self.config("PG_PASS", default="postgres")
            host = self.config("PG_HOST", default="localhost")
            port = self.config("PG_PORT", default="5432")
            database = self.config("PG_NAME", default="postgres")
            self.DATABASE_URL = Secret(
                f"postgresql://{user}:{password}@{host}:{port}/{database}"
            )

        self.CHANNEL_FORTUNKI = self.config("CHANNEL_FORTUNKI")
        self.CHANNEL_COMICS = self.config("CHANNEL_COMICS")
        self.CHANNEL_GEJMING = self.config("CHANNEL_GEJMING")

    async def setup(self):
        self.set_config_vars()
        self.http_client = AsyncClient()

        self.database = Database(self.DATABASE_URL)
        await self.database.connect()

    async def teardown(self):
        await self.http_client.aclose()
        await self.database.disconnect()

    @property
    def uptime(self) -> Optional[timedelta]:
        if self.DEPLOY_TIMESTAMP is None:
            return
        return datetime.utcnow() - datetime.utcfromtimestamp(self.DEPLOY_TIMESTAMP)

    @property
    def b3(self):
        from qbot.backblaze import setup_b3

        if self._b3 is None:
            self._b3 = setup_b3(
                bucket=self.config("B2_BUCKET"),
                app_key_id=self.config("B2_KEY_ID"),
                app_secret_key=str(self.config("B2_SECRET_KEY", cast=Secret)),
            )
        return self._b3


registry = Registry()
