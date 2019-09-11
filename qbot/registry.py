import os

import aiohttp


class Registry:
    async def setup(self):
        self.REVISION = os.environ.get("GIT_REV", "N/A")[:8]
        self.SIGNING_SECRET = os.environ.get("Q_SIGNING_SECRET")
        self.SLACK_TOKEN = os.environ.get("Q_SLACK_TOKEN")

        self.http_session = aiohttp.ClientSession()

    async def teardown(self):
        await self.http_session.close()


registry = Registry()
