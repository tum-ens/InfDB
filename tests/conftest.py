"""Shared pytest configuration and fixtures for the repository."""
import pytest

# Default connection parameters matching a locally running InfDB PostgreSQL instance.
_DB_ENV_DEFAULTS = {
    "SERVICES_POSTGRES_EXPOSED_PORT": "5432",
    "SERVICES_POSTGRES_USER": "infdb",
    "SERVICES_POSTGRES_PASSWORD": "infdb",
    "SERVICES_POSTGRES_DB": "infdb",
    "SERVICES_POSTGRES_EPSG": "25832",
    "SERVICES_POSTGRES_HOST": "localhost",
}


@pytest.fixture
def sample_data():
    """Simple shared fixture used by lightweight tests."""
    return {"foo": "bar", "value": 42}


@pytest.fixture
def db_env(monkeypatch):
    """Sets env variables required by InfdbConfig.get_db_parameters().

    Integration and e2e tests depend on this fixture. When the database is
    unreachable, those tests skip themselves via pytest.skip in their fixture.
    """
    for key, value in _DB_ENV_DEFAULTS.items():
        monkeypatch.setenv(key, value)
