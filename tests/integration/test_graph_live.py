"""Integration tests — live Graph API round-trips.

Requires:
    CORPUS_TOKEN   Bearer token with Mail.ReadWrite delegated permission
    CORPUS_MAILBOX Target mailbox email address

Run with:
    pytest -m integration
"""

import pytest

from cpmf_lo365om_corpus.graph import (
    clear_folder,
    create_message,
    ensure_folder,
    make_client,
)


INTEGRATION_FOLDER = "TestCorpus/IntegrationTests"


@pytest.fixture(scope="module")
def client(token):
    return make_client(token)


@pytest.fixture(scope="module")
def folder_id(client, mailbox):
    """Ensure the integration test folder exists; return its ID."""
    return ensure_folder(client, mailbox, INTEGRATION_FOLDER)


# ── ensure_folder ─────────────────────────────────────────────────────────────

def test_ensure_folder_returns_id(folder_id):
    assert folder_id
    assert isinstance(folder_id, str)


def test_ensure_folder_idempotent(client, mailbox):
    id1 = ensure_folder(client, mailbox, INTEGRATION_FOLDER)
    id2 = ensure_folder(client, mailbox, INTEGRATION_FOLDER)
    assert id1 == id2


# ── create_message ────────────────────────────────────────────────────────────

def test_create_message_returns_id(client, mailbox, folder_id, tmp_path):
    ctx = {
        "run_id":       "integration-test",
        "run_id_short": "inttest",
        "timestamp":    "2026-01-01T00:00:00Z",
        "date":         "20260101",
        "label":        "MSG_LIVE_TEST",
        "index":        0,
        "row_index":    0,
    }
    spec = {
        "label":   "MSG_LIVE_TEST",
        "subject": "Integration test — {label}",
        "from":    "corpus@example.com",
        "to":      [mailbox],
        "body":    {"content": "Live integration test message."},
    }
    msg_id = create_message(client, mailbox, folder_id, spec, ctx, tmp_path)
    assert msg_id
    assert isinstance(msg_id, str)


# ── clear_folder ──────────────────────────────────────────────────────────────

def test_clear_folder_deletes_messages(client, mailbox, folder_id, tmp_path):
    ctx = {
        "run_id": "x", "run_id_short": "x", "timestamp": "x", "date": "x",
        "label": "MSG_CLEAR", "index": 0, "row_index": 0,
    }
    spec = {
        "label": "MSG_CLEAR", "subject": "To be deleted",
        "from": "x@x.com", "to": [mailbox],
        "body": {"content": "delete me"},
    }
    create_message(client, mailbox, folder_id, spec, ctx, tmp_path)
    deleted = clear_folder(client, mailbox, folder_id)
    assert deleted >= 1
