"""Integration tests for InfdbClient — skipped when PostgreSQL is not reachable."""
import logging

import pytest
import sqlalchemy
from infdb.client import InfdbClient
from infdb.config import InfdbConfig
from psycopg2 import OperationalError

pytestmark = pytest.mark.integration


@pytest.fixture
def client(db_env):
    """Yields a connected InfdbClient, or skips if the DB is unreachable."""
    cfg = InfdbConfig(tool_name="test", config_path=None, host="localhost")
    log = logging.getLogger("test-client")
    try:
        c = InfdbClient(cfg, log)
    except OperationalError:
        pytest.skip("PostgreSQL not reachable — skipping integration tests")
    with c:
        yield c


def test_select_one(client):
    rows = client.execute_query("SELECT 1 AS val")
    assert rows == [(1,)]


def test_execute_query_returns_multiple_rows(client):
    rows = client.execute_query("SELECT generate_series(1, 3) AS n")
    assert len(rows) == 3
    assert rows[0][0] == 1


def test_non_select_returns_empty_list(client):
    result = client.execute_query("CREATE TEMP TABLE _pytest_infdb_check (id INT)")
    assert result == []


def test_get_db_params_contains_expected_keys(client):
    params = client.get_db_params()
    for key in ("host", "user", "db", "exposed_port"):
        assert key in params


def test_get_db_engine_returns_engine(client):
    engine = client.get_db_engine()
    assert isinstance(engine, sqlalchemy.engine.Engine)
