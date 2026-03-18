"""Integration test configuration — guards and shared fixtures."""

import os
import pytest


def pytest_collection_modifyitems(items):
    """Auto-apply the 'integration' mark to everything under tests/integration/."""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session")
def token() -> str:
    value = os.environ.get("CORPUS_TOKEN", "")
    if not value:
        pytest.skip("CORPUS_TOKEN not set — skipping integration tests")
    return value


@pytest.fixture(scope="session")
def mailbox() -> str:
    value = os.environ.get("CORPUS_MAILBOX", "")
    if not value:
        pytest.skip("CORPUS_MAILBOX not set — skipping integration tests")
    return value
