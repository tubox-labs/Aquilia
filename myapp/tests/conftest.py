"""
Shared test fixtures for myapp.

Run tests with:
    pytest tests/ -v
"""

import pytest


@pytest.fixture
def app_config():
    """Base application configuration for tests."""
    return {
        "name": "myapp",
        "mode": "test",
        "debug": True,
    }
