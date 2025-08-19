# Pytest configuration and fixtures
# conftest.py

import pytest


# Example: Shared fixture for temporary test data
@pytest.fixture
def sample_data():
    return {"foo": "bar", "value": 42}


# You can add more fixtures or hooks as needed
