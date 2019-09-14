import aiohttp
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.applications import Starlette
from starlette.config import Config
from starlette.datastructures import Secret


# noinspection PyAttributeOutsideInit
class Registry:
    async def setup(self, starlette: Starlette = None):
        self.set_config_vars()
        if self.SENTRY_DSN:
            sentry_sdk.init(dsn=str(self.SENTRY_DSN))
        if self.SENTRY_DSN and starlette:
            SentryAsgiMiddleware(starlette)
        self.http_session = aiohttp.ClientSession()

    def set_config_vars(self):
        config = Config(".env")
        self.REVISION = config("GIT_REV", default="N/A")
        self.SIGNING_SECRET = config("Q_SIGNING_SECRET", cast=Secret)
        self.SLACK_TOKEN = config("Q_SLACK_TOKEN", cast=Secret)
        self.SENTRY_DSN = config("Q_SENTRY_DSN", cast=Secret, default=None)

    async def teardown(self):
        await self.http_session.close()


registry = Registry()
