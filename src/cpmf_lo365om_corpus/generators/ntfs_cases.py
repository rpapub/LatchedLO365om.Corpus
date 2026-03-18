"""NTFS / Windows filename edge-case catalog for LatchedLO365om.

Each entry defines a raw filename (sent as the attachment name in the email)
and the expected sanitised filename that a correct implementation of
GenericMailMessage.SanitizeFileName() should produce.

SanitizeFileName() behaviour (GenericMailMessage.cs):
  1. Remove all chars in Path.GetInvalidFileNameChars():
       control chars \\x00-\\x1f, " * / : < > ? \\ |
  2. If the result is empty or whitespace-only → "unnamed"
  3. If Path.GetFileNameWithoutExtension(result) is a reserved NTFS device name
     (CON PRN AUX NUL COM1-COM9 LPT1-LPT9, case-insensitive) → prepend "_"

Entries where `expected` differs from `raw` reveal gaps in the implementation
and will produce failing tests — which is the point.
"""

from typing import TypedDict


class NtfsCase(TypedDict):
    raw: str
    expected: str
    description: str


NTFS_EDGE_CASES: dict[str, NtfsCase] = {

    # ── Reserved device names ─────────────────────────────────────────────────
    # SanitizeFileName prepends "_" when nameOnly is reserved.

    "reserved_nul": {
        "raw":         "NUL.pdf",
        "expected":    "_NUL.pdf",
        "description": "NTFS reserved device name NUL — must be prefixed",
    },
    "reserved_con": {
        "raw":         "CON.txt",
        "expected":    "_CON.txt",
        "description": "NTFS reserved device name CON",
    },
    "reserved_prn": {
        "raw":         "PRN.xlsx",
        "expected":    "_PRN.xlsx",
        "description": "NTFS reserved device name PRN",
    },
    "reserved_aux": {
        "raw":         "AUX.pdf",
        "expected":    "_AUX.pdf",
        "description": "NTFS reserved device name AUX",
    },
    "reserved_com1": {
        "raw":         "COM1.xlsx",
        "expected":    "_COM1.xlsx",
        "description": "NTFS reserved device name COM1",
    },
    "reserved_lpt1": {
        "raw":         "LPT1.txt",
        "expected":    "_LPT1.txt",
        "description": "NTFS reserved device name LPT1",
    },
    "reserved_mixed_case": {
        "raw":         "nUl.PDF",
        "expected":    "_nUl.PDF",
        "description": "Reserved name check is case-insensitive — nUl must also be prefixed",
    },
    "reserved_no_extension": {
        "raw":         "CON",
        "expected":    "_CON",
        "description": "Reserved name without extension",
    },

    # ── Illegal characters (removed, not replaced) ────────────────────────────
    # SanitizeFileName removes invalid chars — it does NOT replace with "_".

    "illegal_colon": {
        "raw":         "re:port.pdf",
        "expected":    "report.pdf",
        "description": "Colon is invalid on NTFS — removed",
    },
    "illegal_star": {
        "raw":         "file*.txt",
        "expected":    "file.txt",
        "description": "Asterisk is invalid on NTFS — removed",
    },
    "illegal_question": {
        "raw":         "what?.pdf",
        "expected":    "what.pdf",
        "description": "Question mark is invalid on NTFS — removed",
    },
    "illegal_pipe": {
        "raw":         "a|b.txt",
        "expected":    "ab.txt",
        "description": "Pipe is invalid on NTFS — removed",
    },
    "illegal_angles": {
        "raw":         "a<b>.txt",
        "expected":    "ab.txt",
        "description": "Angle brackets are invalid on NTFS — removed",
    },
    "illegal_quote": {
        "raw":         'say"hello".pdf',
        "expected":    "sayhello.pdf",
        "description": "Double quote is invalid on NTFS — removed",
    },
    "illegal_backslash": {
        "raw":         "sub\\file.pdf",
        "expected":    "subfile.pdf",
        "description": "Backslash is invalid in filename — removed",
    },
    "illegal_slash": {
        "raw":         "sub/dir/file.pdf",
        "expected":    "subdirfile.pdf",
        "description": "Forward slash is invalid in filename — removed",
    },
    "illegal_all": {
        "raw":         '/:*?"<>|.txt',
        "expected":    ".txt",
        "description": "All illegal chars stripped — only extension remains",
    },

    # ── Control characters ────────────────────────────────────────────────────
    # \x00-\x1f are all in GetInvalidFileNameChars() on Windows.

    "null_byte": {
        "raw":         "fi\x00le.pdf",
        "expected":    "file.pdf",
        "description": "Null byte (\\x00) is invalid — removed",
    },
    "tab_in_name": {
        "raw":         "re\tport.pdf",
        "expected":    "report.pdf",
        "description": "Tab (\\t, \\x09) is a control char — removed",
    },
    "newline_in_name": {
        "raw":         "re\nport.pdf",
        "expected":    "report.pdf",
        "description": "Newline (\\n, \\x0a) is a control char — removed",
    },

    # ── Whitespace-only result ─────────────────────────────────────────────────
    # After stripping illegal chars, if result is whitespace-only → "unnamed"

    "only_illegal_chars": {
        "raw":         ':|*?"<>',
        "expected":    "unnamed",
        "description": "All chars stripped → whitespace-only → fallback to 'unnamed'",
    },
    "spaces_only": {
        "raw":         "   ",
        "expected":    "unnamed",
        "description": "Spaces are valid chars but result is whitespace-only → 'unnamed'",
    },

    # ── Gaps in SanitizeFileName — these reveal missing coverage ─────────────
    # The following cases are NOT handled by SanitizeFileName. The expected
    # value is what SanitizeFileName currently returns; the actual file write
    # may fail at the OS level or produce a different result.

    "trailing_dot": {
        "raw":         "report.",
        "expected":    "report.",          # SanitizeFileName returns as-is; OS strips trailing dot
        "description": "GAP: trailing dot not stripped by SanitizeFileName — Windows OS strips it silently",
    },
    "trailing_space": {
        "raw":         "report ",
        "expected":    "report ",          # SanitizeFileName returns as-is; OS strips trailing space
        "description": "GAP: trailing space not stripped by SanitizeFileName — Windows OS strips it silently",
    },
    "office_temp_prefix": {
        "raw":         "~$report.docx",
        "expected":    "~$report.docx",   # SanitizeFileName does not handle ~$ prefix
        "description": "GAP: ~$ prefix (Office temp files) not handled by SanitizeFileName",
    },
    "rtl_override": {
        "raw":         "evil\u202Etxt.exe",
        "expected":    "evil\u202Etxt.exe",  # U+202E not in GetInvalidFileNameChars
        "description": "GAP: RTL override character (U+202E) not stripped — visual filename spoofing risk",
    },
    "zero_width_space": {
        "raw":         "fi\u200Ble.pdf",
        "expected":    "fi\u200Ble.pdf",    # U+200B not in GetInvalidFileNameChars
        "description": "GAP: zero-width space (U+200B) not stripped — creates invisible chars in filename",
    },

    # ── Unicode — valid on NTFS ───────────────────────────────────────────────

    "emoji": {
        "raw":         "📎attachment.pdf",
        "expected":    "📎attachment.pdf",
        "description": "Emoji (U+1F4CE) is valid on NTFS — kept as-is",
    },
    "arabic": {
        "raw":         "تقرير.pdf",
        "expected":    "تقرير.pdf",
        "description": "Arabic script is valid on NTFS — kept as-is",
    },
    "mixed_script": {
        "raw":         "fileファイル.pdf",
        "expected":    "fileファイル.pdf",
        "description": "Mixed Latin + CJK script is valid on NTFS — kept as-is",
    },

    # ── Length edge cases ─────────────────────────────────────────────────────
    # SanitizeFileName itself does not truncate. Length truncation happens
    # in SaveAsEml based on full path length (260-char limit).

    "max_component_length": {
        "raw":         "a" * 251 + ".pdf",   # 255 chars — NTFS component limit
        "expected":    "a" * 251 + ".pdf",
        "description": "Filename at NTFS 255-char component limit — kept as-is by SanitizeFileName",
    },
    "over_component_length": {
        "raw":         "a" * 252 + ".pdf",   # 256 chars — over limit
        "expected":    "a" * 252 + ".pdf",   # SanitizeFileName doesn't truncate; SaveAsEml does
        "description": "GAP: SanitizeFileName does not truncate; SaveAsEml truncates based on full path",
    },

    # ── Extension edge cases ──────────────────────────────────────────────────

    "no_extension": {
        "raw":         "README",
        "expected":    "README",
        "description": "No extension — valid, kept as-is",
    },
    "double_extension": {
        "raw":         "file.tar.gz",
        "expected":    "file.tar.gz",
        "description": "Double extension — kept as-is; GetFileNameWithoutExtension returns 'file.tar'",
    },
    "only_extension": {
        "raw":         ".pdf",
        "expected":    ".pdf",
        "description": "Starts with dot, no stem — not reserved, kept as-is",
    },
    "leading_spaces": {
        "raw":         "   report.pdf",
        "expected":    "   report.pdf",
        "description": "Leading spaces are valid chars — kept as-is by SanitizeFileName",
    },
}


def resolve(spec: dict) -> tuple[str, str]:
    """Return (raw_name, expected_name) for the given spec.

    spec:
      strategy: ntfs_edge_case
      case: reserved_nul

    Returns:
        (raw, expected) — raw is placed in the email attachment;
        expected is written into corpus.json for test assertions.

    Raises:
        ValueError if case is missing or unknown.
    """
    case = spec.get("case")
    if not case:
        raise ValueError("ntfs_edge_case strategy requires a 'case' key")
    if case not in NTFS_EDGE_CASES:
        available = sorted(NTFS_EDGE_CASES)
        raise ValueError(f"Unknown ntfs_edge_case: {case!r}. Available: {available}")
    entry = NTFS_EDGE_CASES[case]
    return entry["raw"], entry["expected"]
