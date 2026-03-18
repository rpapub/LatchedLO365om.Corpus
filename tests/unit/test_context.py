"""Unit tests for context.py — template substitution."""

import pytest

from cpmf_lo365om_corpus.context import make_context, t, t_deep


# ── t() ───────────────────────────────────────────────────────────────────────

def test_t_substitutes_known_key(ctx):
    result = t("Run: {run_id}", ctx)
    assert result == "Run: test-run-00000000"


def test_t_substitutes_multiple_keys(ctx):
    result = t("{label}_{index}", ctx)
    assert result == "MSG_TEST_0"


def test_t_passthrough_no_placeholders(ctx):
    assert t("plain string", ctx) == "plain string"


def test_t_empty_string(ctx):
    assert t("", ctx) == ""


def test_t_non_string_passthrough(ctx):
    assert t(42, ctx) == 42
    assert t(None, ctx) is None


def test_t_row_index_override(ctx):
    result = t("row {row_index}", ctx, row_index=7)
    assert result == "row 7"


def test_t_missing_key_raises(ctx):
    with pytest.raises(KeyError):
        t("{nonexistent_key}", ctx)


# ── t_deep() ──────────────────────────────────────────────────────────────────

def test_t_deep_string(ctx):
    assert t_deep("label={label}", ctx) == "label=MSG_TEST"


def test_t_deep_dict(ctx):
    result = t_deep({"a": "{label}", "b": "static"}, ctx)
    assert result == {"a": "MSG_TEST", "b": "static"}


def test_t_deep_list(ctx):
    result = t_deep(["{label}", "{date}"], ctx)
    assert result == ["MSG_TEST", "20260101"]


def test_t_deep_nested(ctx):
    result = t_deep({"outer": {"inner": "{run_id_short}"}}, ctx)
    assert result == {"outer": {"inner": "test-run"}}


def test_t_deep_passthrough_non_string(ctx):
    assert t_deep(123, ctx) == 123
    assert t_deep(None, ctx) is None


# ── make_context() ────────────────────────────────────────────────────────────

def test_make_context_shape():
    ctx = make_context("abc-123", "2026-01-01T00:00:00Z", "20260101",
                       label="X", index=3)
    assert ctx["run_id"]       == "abc-123"
    assert ctx["run_id_short"] == "abc-123"[:8]
    assert ctx["timestamp"]    == "2026-01-01T00:00:00Z"
    assert ctx["date"]         == "20260101"
    assert ctx["label"]        == "X"
    assert ctx["index"]        == 3
    assert ctx["row_index"]    == 0


def test_make_context_run_id_short_truncates():
    ctx = make_context("abcdefgh-1234-5678", "t", "d")
    assert ctx["run_id_short"] == "abcdefgh"
