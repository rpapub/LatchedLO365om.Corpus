"""Unit tests for generators/ntfs_cases.py."""

import pytest

from cpmf_lo365om_corpus.generators.ntfs_cases import NTFS_EDGE_CASES, resolve


# ── catalog integrity ─────────────────────────────────────────────────────────

def test_catalog_nonempty():
    assert len(NTFS_EDGE_CASES) > 0


@pytest.mark.parametrize("case_key, entry", NTFS_EDGE_CASES.items())
def test_every_case_has_required_keys(case_key, entry):
    assert "raw" in entry,         f"{case_key}: missing 'raw'"
    assert "expected" in entry,    f"{case_key}: missing 'expected'"
    assert "description" in entry, f"{case_key}: missing 'description'"


@pytest.mark.parametrize("case_key, entry", NTFS_EDGE_CASES.items())
def test_every_case_has_nonempty_strings(case_key, entry):
    assert isinstance(entry["raw"], str),         f"{case_key}: raw must be str"
    assert isinstance(entry["expected"], str),     f"{case_key}: expected must be str"
    assert isinstance(entry["description"], str),  f"{case_key}: description must be str"
    assert entry["raw"],         f"{case_key}: raw must not be empty"
    assert entry["description"], f"{case_key}: description must not be empty"
    # expected may be empty string (e.g. all-illegal-chars case produces "" or "unnamed")


# ── resolve() happy path ──────────────────────────────────────────────────────

@pytest.mark.parametrize("case_key", NTFS_EDGE_CASES)
def test_resolve_returns_correct_tuple_for_all_cases(case_key):
    spec = {"strategy": "ntfs_edge_case", "case": case_key}
    raw, expected = resolve(spec)
    assert raw      == NTFS_EDGE_CASES[case_key]["raw"]
    assert expected == NTFS_EDGE_CASES[case_key]["expected"]


# ── resolve() spot-checks by category ────────────────────────────────────────

def test_reserved_nul_prefixed():
    raw, expected = resolve({"strategy": "ntfs_edge_case", "case": "reserved_nul"})
    assert raw == "NUL.pdf"
    assert expected == "_NUL.pdf"


def test_reserved_mixed_case_prefixed():
    raw, expected = resolve({"strategy": "ntfs_edge_case", "case": "reserved_mixed_case"})
    assert raw == "nUl.PDF"
    assert expected == "_nUl.PDF"


def test_reserved_no_extension():
    raw, expected = resolve({"strategy": "ntfs_edge_case", "case": "reserved_no_extension"})
    assert raw == "CON"
    assert expected == "_CON"


def test_illegal_colon_removed():
    raw, expected = resolve({"strategy": "ntfs_edge_case", "case": "illegal_colon"})
    assert ":" in raw
    assert ":" not in expected


def test_illegal_all_chars_stripped():
    raw, expected = resolve({"strategy": "ntfs_edge_case", "case": "illegal_all"})
    assert expected == ".txt"


def test_only_illegal_chars_fallback_to_unnamed():
    raw, expected = resolve({"strategy": "ntfs_edge_case", "case": "only_illegal_chars"})
    assert expected == "unnamed"


def test_spaces_only_fallback_to_unnamed():
    raw, expected = resolve({"strategy": "ntfs_edge_case", "case": "spaces_only"})
    assert expected == "unnamed"


def test_control_null_byte_removed():
    raw, expected = resolve({"strategy": "ntfs_edge_case", "case": "null_byte"})
    assert "\x00" in raw
    assert "\x00" not in expected


def test_gap_trailing_dot_unchanged():
    """SanitizeFileName does not strip trailing dots — OS does it silently."""
    raw, expected = resolve({"strategy": "ntfs_edge_case", "case": "trailing_dot"})
    assert raw == expected   # GAP: raw == expected means implementation leaves it


def test_gap_rtl_override_unchanged():
    raw, expected = resolve({"strategy": "ntfs_edge_case", "case": "rtl_override"})
    assert "\u202e" in raw
    assert raw == expected   # GAP: RTL override not stripped


def test_unicode_emoji_preserved():
    raw, expected = resolve({"strategy": "ntfs_edge_case", "case": "emoji"})
    assert raw == expected
    assert "📎" in expected


def test_unicode_arabic_preserved():
    raw, expected = resolve({"strategy": "ntfs_edge_case", "case": "arabic"})
    assert raw == expected


# ── resolve() error handling ──────────────────────────────────────────────────

def test_resolve_raises_for_missing_case_key():
    with pytest.raises(ValueError, match="requires a 'case' key"):
        resolve({"strategy": "ntfs_edge_case"})


def test_resolve_raises_for_unknown_case():
    with pytest.raises(ValueError, match="Unknown ntfs_edge_case"):
        resolve({"strategy": "ntfs_edge_case", "case": "does_not_exist"})


def test_resolve_error_lists_available_cases():
    with pytest.raises(ValueError) as exc:
        resolve({"strategy": "ntfs_edge_case", "case": "does_not_exist"})
    assert "reserved_nul" in str(exc.value)
