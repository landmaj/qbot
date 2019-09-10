import os


class Registry:
    def __init__(self):
        self.REVISION = os.environ.get("GIT_REV", "N/A")[:8]
        self.SIGNING_SECRET = os.environ.get("Q_SIGNING_SECRET")
        self.SLACK_TOKEN = os.environ.get("Q_SLACK_TOKEN")


registry = Registry()
