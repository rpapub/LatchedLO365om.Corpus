"""Unit tests for body.py — body rendering and field extraction."""

import pytest

from cpmf_lo365om_corpus.body import (
    build_body,
    extract_structured_fields,
    get_separator,
    resolve_value,
)


# ── resolve_value() ───────────────────────────────────────────────────────────

def test_resolve_value_plain_string(ctx):
    assert resolve_value("hello {label}", ctx) == "hello MSG_TEST"


def test_resolve_value_plain_string_no_placeholders(ctx):
    assert resolve_value("static", ctx) == "static"


def test_resolve_value_faker_strategy(ctx):
    result = resolve_value({"strategy": "faker", "method": "name", "seed": 1}, ctx)
    assert isinstance(result, str)
    assert result


def test_resolve_value_unknown_strategy_raises(ctx):
    with pytest.raises(ValueError, match="Unknown value generation strategy"):
        resolve_value({"strategy": "unknown_xyz"}, ctx)


# ── build_body() ──────────────────────────────────────────────────────────────

def test_build_body_none_returns_empty_text(ctx):
    content_type, content = build_body(None, ctx)
    assert content_type == "text"
    assert content == ""


def test_build_body_raw_content(ctx):
    spec = {"content": "Hello {label}"}
    content_type, content = build_body(spec, ctx)
    assert content_type == "text"
    assert content == "Hello MSG_TEST"


def test_build_body_raw_content_html(ctx):
    spec = {"contentType": "html", "content": "<b>{label}</b>"}
    content_type, content = build_body(spec, ctx)
    assert content_type == "html"
    assert content == "<b>MSG_TEST</b>"


def test_build_body_header_section(ctx):
    spec = {
        "sections": [
            {"type": "header", "content": "=== {label} ==="},
        ]
    }
    _, content = build_body(spec, ctx)
    assert content == "=== MSG_TEST ==="


def test_build_body_structured_section(ctx):
    spec = {
        "sections": [
            {
                "type": "structured",
                "separator": ": ",
                "fields": [
                    {"key": "Label", "value": "{label}"},
                    {"key": "Date",  "value": "{date}"},
                ],
            }
        ]
    }
    _, content = build_body(spec, ctx)
    assert "Label: MSG_TEST" in content
    assert "Date: 20260101" in content


def test_build_body_multiple_sections_joined_by_newline(ctx):
    spec = {
        "sections": [
            {"type": "header",     "content": "HEADER"},
            {"type": "structured", "separator": ": ", "fields": [{"key": "K", "value": "V"}]},
            {"type": "footer",     "content": "FOOTER"},
        ]
    }
    _, content = build_body(spec, ctx)
    lines = content.split("\n")
    assert lines[0] == "HEADER"
    assert lines[1] == "K: V"
    assert lines[2] == "FOOTER"


def test_build_body_unknown_section_type_raises(ctx):
    spec = {"sections": [{"type": "weird_type", "content": "x"}]}
    with pytest.raises(ValueError, match="Unknown body section type"):
        build_body(spec, ctx)


def test_build_body_structured_faker_value(ctx):
    spec = {
        "sections": [
            {
                "type": "structured",
                "separator": ": ",
                "fields": [
                    {"key": "Company", "value": {"strategy": "faker", "method": "company", "seed": 7}},
                ],
            }
        ]
    }
    _, content = build_body(spec, ctx)
    assert "Company: " in content


# ── extract_structured_fields() ───────────────────────────────────────────────

def test_extract_structured_fields_returns_empty_for_none(ctx):
    assert extract_structured_fields(None, ctx) == {}


def test_extract_structured_fields_returns_empty_for_raw_content(ctx):
    assert extract_structured_fields({"content": "raw"}, ctx) == {}


def test_extract_structured_fields_returns_resolved_pairs(ctx):
    spec = {
        "sections": [
            {
                "type": "structured",
                "separator": ": ",
                "fields": [
                    {"key": "Label", "value": "{label}"},
                    {"key": "Index", "value": "{index}"},
                ],
            }
        ]
    }
    fields = extract_structured_fields(spec, ctx)
    assert fields == {"Label": "MSG_TEST", "Index": "0"}


def test_extract_structured_fields_skips_non_structured_sections(ctx):
    spec = {
        "sections": [
            {"type": "header", "content": "ignore me"},
            {"type": "structured", "separator": ": ", "fields": [{"key": "K", "value": "V"}]},
            {"type": "footer", "content": "ignore me too"},
        ]
    }
    fields = extract_structured_fields(spec, ctx)
    assert list(fields.keys()) == ["K"]


# ── get_separator() ───────────────────────────────────────────────────────────

def test_get_separator_default_when_no_spec():
    assert get_separator(None) == ": "


def test_get_separator_default_when_no_sections():
    assert get_separator({"content": "raw"}) == ": "


def test_get_separator_from_first_structured_section():
    spec = {
        "sections": [
            {"type": "header", "content": "h"},
            {"type": "structured", "separator": " = ", "fields": []},
        ]
    }
    assert get_separator(spec) == " = "


def test_get_separator_default_when_no_structured_section():
    spec = {"sections": [{"type": "header", "content": "h"}]}
    assert get_separator(spec) == ": "
