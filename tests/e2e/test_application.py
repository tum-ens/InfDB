"""End-to-end smoke tests for the InfDB facade — skipped when PostgreSQL is not reachable."""
import logging

import pytest
import yaml
from pyinfdb import InfDB
from psycopg2 import OperationalError

pytestmark = pytest.mark.e2e


@pytest.fixture
def infdb(tmp_path, db_env):
    """Yields a fully initialised InfDB; skips if the DB is unreachable."""
    log_file = str(tmp_path / "e2e-tool.log")
    config = {"e2e-tool": {"logging": {"path": log_file, "level": "INFO"}}}
    config_path = str(tmp_path / "config-e2e-tool.yml")
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)

    instance = InfDB(tool_name="e2e-tool", config_path=config_path, host="localhost")
    try:
        with instance.connect() as c:
            c.execute_query("SELECT 1")
    except OperationalError:
        instance.stop_logger()
        pytest.skip("PostgreSQL not reachable — skipping e2e tests")

    yield instance
    instance.stop_logger()


def test_str_contains_tool_name(infdb):
    assert "e2e-tool" in str(infdb)


def test_get_toolname(infdb):
    assert infdb.get_toolname() == "e2e-tool"


def test_get_logger_returns_logger(infdb):
    assert isinstance(infdb.get_logger(), logging.Logger)


def test_connect_and_query(infdb):
    with infdb.connect() as client:
        rows = client.execute_query("SELECT 1")
    assert rows == [(1,)]


def test_get_config_value(infdb):
    level = infdb.get_config_value(["logging", "level"], insert_toolname=True)
    assert level == "INFO"
