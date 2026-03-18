"""Unit tests for manifest.py — build_manifest() output shape."""

import pytest

from cpmf_lo365om_corpus.manifest import build_manifest, SCHEMA_VERSION


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_entry(label="MSG_A", subject="Subject {label}", attachments=None, body=None):
    msg_spec = {"subject": subject}
    if attachments is not None:
        msg_spec["attachments"] = attachments
    if body is not None:
        msg_spec["body"] = body
    return {
        "label":        label,
        "immutable_id": f"IMM_{label}",
        "msg_spec":     msg_spec,
        "ctx": {
            "run_id":       "run-001",
            "run_id_short": "run-001",
            "timestamp":    "2026-01-01T00:00:00Z",
            "date":         "20260101",
            "label":        label,
            "index":        0,
            "row_index":    0,
        },
        "folder_path": "TestCorpus/Mail",
    }


# ── top-level shape ───────────────────────────────────────────────────────────

def test_build_manifest_top_level_keys():
    manifest = build_manifest(
        run_id="run-001",
        timestamp="2026-01-01T00:00:00Z",
        mailbox="test@example.com",
        workload="mail",
        folders={"TestCorpus/Mail": "folder-id-123"},
        messages_created=[],
        expected_spec={},
    )
    assert manifest["schema_version"] == SCHEMA_VERSION
    assert manifest["run_id"]         == "run-001"
    assert manifest["created_at"]     == "2026-01-01T00:00:00Z"
    assert manifest["mailbox"]        == "test@example.com"
    assert manifest["workload"]       == "mail"
    assert manifest["folders"]        == {"TestCorpus/Mail": "folder-id-123"}
    assert manifest["messages"]       == {}


def test_build_manifest_message_shape():
    entry = _make_entry("MSG_A", "Hello {label}")
    manifest = build_manifest(
        run_id="r", timestamp="t", mailbox="m", workload="mail",
        folders={"TestCorpus/Mail": "fid"},
        messages_created=[entry],
        expected_spec={},
    )
    msg = manifest["messages"]["MSG_A"]
    assert msg["immutableId"]  == "IMM_MSG_A"
    assert msg["subject"]      == "Hello MSG_A"
    assert msg["sourceFolder"] == "TestCorpus/Mail"
    assert "body"              in msg
    assert "attachments"       in msg
    assert "expected"          in msg


# ── attachments in manifest ───────────────────────────────────────────────────

def test_build_manifest_no_attachments_yields_empty_list():
    entry = _make_entry("MSG_B")
    manifest = build_manifest(
        run_id="r", timestamp="t", mailbox="m", workload="mail",
        folders={"TestCorpus/Mail": "fid"},
        messages_created=[entry],
        expected_spec={},
    )
    assert manifest["messages"]["MSG_B"]["attachments"] == []


def test_build_manifest_plain_name_attachment_no_expected_name():
    entry = _make_entry("MSG_C", attachments=[{"name": "file.txt"}])
    manifest = build_manifest(
        run_id="r", timestamp="t", mailbox="m", workload="mail",
        folders={"TestCorpus/Mail": "fid"},
        messages_created=[entry],
        expected_spec={},
    )
    atts = manifest["messages"]["MSG_C"]["attachments"]
    assert len(atts) == 1
    assert atts[0]["raw_name"] == "file.txt"
    assert "expected_name" not in atts[0]


def test_build_manifest_ntfs_strategy_attachment_has_expected_name():
    entry = _make_entry("MSG_D", attachments=[
        {"name": {"strategy": "ntfs_edge_case", "case": "reserved_nul"}}
    ])
    manifest = build_manifest(
        run_id="r", timestamp="t", mailbox="m", workload="mail",
        folders={"TestCorpus/Mail": "fid"},
        messages_created=[entry],
        expected_spec={},
    )
    atts = manifest["messages"]["MSG_D"]["attachments"]
    assert atts[0]["raw_name"]      == "NUL.pdf"
    assert atts[0]["expected_name"] == "_NUL.pdf"


def test_build_manifest_multiple_attachments():
    entry = _make_entry("MSG_E", attachments=[
        {"name": "plain.txt"},
        {"name": {"strategy": "ntfs_edge_case", "case": "illegal_colon"}},
    ])
    manifest = build_manifest(
        run_id="r", timestamp="t", mailbox="m", workload="mail",
        folders={"TestCorpus/Mail": "fid"},
        messages_created=[entry],
        expected_spec={},
    )
    atts = manifest["messages"]["MSG_E"]["attachments"]
    assert len(atts) == 2
    assert atts[0]["raw_name"] == "plain.txt"
    assert "expected_name" not in atts[0]
    assert atts[1]["raw_name"] == "re:port.pdf"
    assert atts[1]["expected_name"] == "report.pdf"


# ── expected spec ─────────────────────────────────────────────────────────────

def test_build_manifest_expected_spec_merged():
    entry = _make_entry("MSG_F")
    manifest = build_manifest(
        run_id="r", timestamp="t", mailbox="m", workload="mail",
        folders={"TestCorpus/Mail": "fid"},
        messages_created=[entry],
        expected_spec={"MSG_F": {"savedAttachments": 1}},
    )
    assert manifest["messages"]["MSG_F"]["expected"] == {"savedAttachments": 1}


def test_build_manifest_expected_spec_missing_label_yields_empty():
    entry = _make_entry("MSG_G")
    manifest = build_manifest(
        run_id="r", timestamp="t", mailbox="m", workload="mail",
        folders={"TestCorpus/Mail": "fid"},
        messages_created=[entry],
        expected_spec={},
    )
    assert manifest["messages"]["MSG_G"]["expected"] == {}


# ── multiple messages ─────────────────────────────────────────────────────────

def test_build_manifest_multiple_messages():
    entries = [_make_entry(f"MSG_{i}") for i in range(5)]
    manifest = build_manifest(
        run_id="r", timestamp="t", mailbox="m", workload="mail",
        folders={"TestCorpus/Mail": "fid"},
        messages_created=entries,
        expected_spec={},
    )
    assert len(manifest["messages"]) == 5
    assert "MSG_0" in manifest["messages"]
    assert "MSG_4" in manifest["messages"]
