import pytest
from starlette.config import environ
from starlette.testclient import TestClient

from qbot.app import app


@pytest.fixture(autouse=True, scope="session")
def environmental_variables():
    environ["GIT_REV"] = "TESTING"
    environ["Q_SIGNING_SECRET"] = "SIGNING_SECRET"
    environ["Q_SLACK_TOKEN"] = "SLACK_TOKEN"


@pytest.fixture()
def client():
    # Context Manager is required to execute event handlers
    with TestClient(app) as clnt:
        yield clnt
