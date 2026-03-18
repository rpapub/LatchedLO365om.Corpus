"""Unit tests for generators/faker_gen.py."""

import pytest

from cpmf_lo365om_corpus.generators.faker_gen import resolve


# ── basic resolution ──────────────────────────────────────────────────────────

def test_resolve_returns_string():
    result = resolve({"strategy": "faker", "method": "name"})
    assert isinstance(result, str)
    assert result  # non-empty


def test_resolve_company():
    result = resolve({"strategy": "faker", "method": "company"})
    assert isinstance(result, str)
    assert result


def test_resolve_email():
    result = resolve({"strategy": "faker", "method": "email"})
    assert "@" in result


def test_resolve_sentence():
    result = resolve({"strategy": "faker", "method": "sentence"})
    assert isinstance(result, str)
    assert len(result) > 5


# ── locale ────────────────────────────────────────────────────────────────────

def test_resolve_default_locale_en_us():
    # Should not raise
    result = resolve({"strategy": "faker", "method": "city"})
    assert isinstance(result, str)


def test_resolve_german_locale():
    result = resolve({"strategy": "faker", "method": "city", "locale": "de_DE"})
    assert isinstance(result, str)
    assert result


# ── seed reproducibility ──────────────────────────────────────────────────────

def test_seeded_calls_are_reproducible():
    spec = {"strategy": "faker", "method": "name", "seed": 42}
    first  = resolve(spec)
    second = resolve(spec)
    assert first == second


def test_different_seeds_likely_differ():
    a = resolve({"strategy": "faker", "method": "name", "seed": 1})
    b = resolve({"strategy": "faker", "method": "name", "seed": 9999})
    # Very unlikely to collide; if this flakes, pick different seeds
    assert a != b


# ── error handling ────────────────────────────────────────────────────────────

def test_resolve_raises_for_missing_method():
    with pytest.raises((KeyError, AttributeError)):
        resolve({"strategy": "faker"})


def test_resolve_raises_for_unknown_method():
    with pytest.raises(AttributeError):
        resolve({"strategy": "faker", "method": "this_method_does_not_exist_xyz"})
