"""Unit tests for attachments.py — name resolution."""

import pytest
from pathlib import Path

from cpmf_lo365om_corpus.attachments import build_attachment, resolve_name


# ── resolve_name() — plain strings ────────────────────────────────────────────

def test_resolve_name_plain_string_no_placeholders(ctx):
    raw, expected = resolve_name("report.pdf", ctx)
    assert raw == "report.pdf"
    assert expected is None


def test_resolve_name_plain_string_with_template(ctx):
    raw, expected = resolve_name("report_{date}.pdf", ctx)
    assert raw == "report_20260101.pdf"
    assert expected is None


def test_resolve_name_plain_string_label_substitution(ctx):
    raw, expected = resolve_name("{label}.txt", ctx)
    assert raw == "MSG_TEST.txt"
    assert expected is None


# ── resolve_name() — ntfs_edge_case strategy ──────────────────────────────────

def test_resolve_name_ntfs_strategy_returns_raw_and_expected(ctx):
    spec = {"strategy": "ntfs_edge_case", "case": "reserved_nul"}
    raw, expected = resolve_name(spec, ctx)
    assert raw == "NUL.pdf"
    assert expected == "_NUL.pdf"


def test_resolve_name_ntfs_illegal_colon(ctx):
    spec = {"strategy": "ntfs_edge_case", "case": "illegal_colon"}
    raw, expected = resolve_name(spec, ctx)
    assert ":" in raw
    assert ":" not in expected


def test_resolve_name_ntfs_gap_case_raw_equals_expected(ctx):
    """GAP cases: expected == raw because SanitizeFileName does not handle them."""
    spec = {"strategy": "ntfs_edge_case", "case": "trailing_dot"}
    raw, expected = resolve_name(spec, ctx)
    assert raw == expected


# ── resolve_name() — error handling ──────────────────────────────────────────

def test_resolve_name_unknown_strategy_raises(ctx):
    with pytest.raises(ValueError, match="Unknown name generation strategy"):
        resolve_name({"strategy": "unknown_xyz"}, ctx)


def test_resolve_name_ntfs_unknown_case_raises(ctx):
    with pytest.raises(ValueError, match="Unknown ntfs_edge_case"):
        resolve_name({"strategy": "ntfs_edge_case", "case": "does_not_exist"}, ctx)


# ── build_attachment() ────────────────────────────────────────────────────────

def test_build_attachment_plain_name_text(ctx, tmp_path):
    spec = {
        "name": "hello.txt",
        "strategy": "generate_text",
        "content": "test content",
    }
    att = build_attachment(spec, ctx, tmp_path)
    assert att["name"] == "hello.txt"
    assert att["contentType"] == "text/plain"
    assert att["@odata.type"] == "#microsoft.graph.fileAttachment"
    assert att["contentBytes"]  # base64 non-empty


def test_build_attachment_ntfs_edge_case_name(ctx, tmp_path):
    spec = {
        "name": {"strategy": "ntfs_edge_case", "case": "reserved_nul"},
        "strategy": "generate_text",
        "content": "payload",
    }
    att = build_attachment(spec, ctx, tmp_path)
    assert att["name"] == "NUL.pdf"   # raw name is sent to Graph
    assert att["contentType"] == "application/pdf"


def test_build_attachment_template_name(ctx, tmp_path):
    spec = {
        "name": "attachment_{index}.txt",
        "strategy": "generate_text",
        "content": "data",
    }
    att = build_attachment(spec, ctx, tmp_path)
    assert att["name"] == "attachment_0.txt"


def test_build_attachment_unknown_strategy_raises(ctx, tmp_path):
    spec = {
        "name": "file.txt",
        "strategy": "no_such_strategy",
    }
    with pytest.raises(ValueError, match="Unknown attachment strategy"):
        build_attachment(spec, ctx, tmp_path)


def test_build_attachment_fixture_file_not_found_raises(ctx, tmp_path):
    spec = {
        "name": "file.pdf",
        "strategy": "fixture_file",
        "path": "fixtures/nonexistent.pdf",
    }
    with pytest.raises(FileNotFoundError):
        build_attachment(spec, ctx, tmp_path)
