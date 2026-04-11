"""noqa directive parsing for inline and file-level suppression."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Matches an inline `# noqa` directive anywhere in a line.
# Optional `: CODE1, CODE2` part captures specific codes to suppress.
_RE_INLINE_NOQA: re.Pattern[str] = re.compile(
    r"#\s*noqa\b(?:\s*:\s*(?P<codes>[^#\n]+))?",
    re.IGNORECASE,
)

# Matches a file-level `# pydocfix: noqa` directive (must start the line,
# possibly after leading whitespace — i.e., it must be on its own line).
_RE_FILE_NOQA: re.Pattern[str] = re.compile(
    r"^\s*#\s*pydocfix\s*:\s*noqa\b(?:\s*:\s*(?P<codes>[^#\n]+))?",
    re.IGNORECASE,
)

# Extracts individual rule codes (e.g. PRM001, SUM002) from raw text.
_RE_CODE: re.Pattern[str] = re.compile(r"[A-Za-z]{2,5}\d{3}")


def _parse_codes(raw: str) -> frozenset[str]:
    """Extract and normalise rule codes from a raw comma/space-separated string."""
    return frozenset(c.upper() for c in _RE_CODE.findall(raw))


@dataclass(frozen=True)
class NoqaDirective:
    """A parsed noqa suppression directive.

    ``codes=None`` means suppress *all* rules (blanket suppression).
    ``codes=frozenset(...)`` means suppress only the listed rule codes.
    """

    codes: frozenset[str] | None

    def suppresses(self, code: str) -> bool:
        """Return True if this directive suppresses *code*."""
        return self.codes is None or code.upper() in self.codes


def parse_inline_noqa(line: str) -> NoqaDirective | None:
    """Parse an inline ``# noqa`` directive from a single source line.

    For docstrings, *line* should be the line containing the closing
    triple-quote (``\"\"\"  # noqa: PRM001``).

    Returns ``None`` when no ``noqa`` directive is present.
    """
    m = _RE_INLINE_NOQA.search(line)
    if m is None:
        return None
    raw_codes = m.group("codes")
    if not raw_codes or not raw_codes.strip():
        # Blanket suppression: `# noqa` with nothing after
        return NoqaDirective(codes=None)
    codes = _parse_codes(raw_codes)
    if not codes:
        # Codes section present but no valid codes found — treat as blanket
        return NoqaDirective(codes=None)
    return NoqaDirective(codes=codes)


def find_inline_noqa(line: str) -> tuple[NoqaDirective, tuple[int, int]] | None:
    """Like ``parse_inline_noqa`` but also returns the ``(start, end)`` character span.

    The span is the start and end character positions of the ``# noqa`` match
    within *line*, suitable for computing byte offsets into the source file.

    Returns ``None`` when no ``noqa`` directive is present.
    """
    m = _RE_INLINE_NOQA.search(line)
    if m is None:
        return None
    raw_codes = m.group("codes")
    if not raw_codes or not raw_codes.strip():
        return NoqaDirective(codes=None), (m.start(), m.end())
    codes = _parse_codes(raw_codes)
    if not codes:
        return NoqaDirective(codes=None), (m.start(), m.end())
    return NoqaDirective(codes=codes), (m.start(), m.end())


def parse_file_noqa(lines: list[str]) -> NoqaDirective | None:
    """Scan *lines* for a file-level ``# pydocfix: noqa`` directive.

    The directive must occupy its own line (not follow code) so that it is
    unambiguous.  Returns ``None`` when no such directive is found.
    """
    for line in lines:
        m = _RE_FILE_NOQA.match(line)
        if m is None:
            continue
        raw_codes = m.group("codes")
        if not raw_codes or not raw_codes.strip():
            return NoqaDirective(codes=None)
        codes = _parse_codes(raw_codes)
        if not codes:
            return NoqaDirective(codes=None)
        return NoqaDirective(codes=codes)
    return None
