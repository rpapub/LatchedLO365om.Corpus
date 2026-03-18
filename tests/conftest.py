"""Shared fixtures for all test layers."""

import pytest


@pytest.fixture()
def ctx():
    """Minimal but complete template context for unit tests."""
    return {
        "run_id":       "test-run-00000000",
        "run_id_short": "test-run",
        "timestamp":    "2026-01-01T00:00:00Z",
        "date":         "20260101",
        "label":        "MSG_TEST",
        "index":        0,
        "row_index":    0,
    }
