import pytest
from sqlalchemy import create_engine
from starlette.config import environ
from starlette.testclient import TestClient

from qbot.app import app
from qbot.core import registry
from qbot.db import metadata


@pytest.fixture(autouse=True, scope="session")
def configuration():
    environ["GIT_REV"] = "TESTING"
    environ["Q_SIGNING_SECRET"] = "SIGNING_SECRET"
    environ["Q_SLACK_TOKEN"] = "SLACK_TOKEN"
    environ["DATABASE_URL"] = "sqlite:///test.db"
    environ["TESTING"] = "True"
    registry.set_config_vars()


@pytest.fixture(autouse=True, scope="session")
def create_tables(configuration):
    engine = create_engine(str(registry.DATABASE_URL))
    metadata.create_all(engine)


@pytest.fixture()
def client():
    # Context Manager is required to execute event handlers
    with TestClient(app) as clnt:
        yield clnt
