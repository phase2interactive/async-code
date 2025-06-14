"""
Pytest configuration for all tests
"""
import pytest

# Configure anyio to only use asyncio backend
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"