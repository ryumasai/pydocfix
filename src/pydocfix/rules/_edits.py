"""Edit creation and application utilities."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import pairwise
from typing import Final

from pydocstring import Token

from pydocfix.rules._types import Edit


def replace_token(token: Token, new_text: str) -> Edit:
    """Replace a token's entire text."""
    return Edit(start=token.range.start, end=token.range.end, new_text=new_text)


def insert_at(offset: int, text: str) -> Edit:
    """Insert text at a byte offset (no deletion)."""
    return Edit(start=offset, end=offset, new_text=text)


def delete_range(start: int, end: int) -> Edit:
    """Delete a byte range."""
    return Edit(start=start, end=end, new_text="")


def detect_section_indent(ds_text: str, stmt_col_offset: int = 0) -> str:
    """Detect the section-level indentation from docstring content.

    For multiline docstrings the last line is typically only whitespace
    (the indent before the closing triple-quote) and directly gives the
    section indent.  Otherwise the first non-empty indented line after the
    summary is used, falling back to *stmt_col_offset* spaces.
    """
    lines = ds_text.split("\n")
    if len(lines) > 1:
        last = lines[-1]
        if not last.strip():
            return last
        for line in lines[1:]:
            if line and not line.isspace():
                n = len(line) - len(line.lstrip(" \t"))
                if n > 0:
                    return line[:n]
    return " " * stmt_col_offset


def section_append_edit(ds_text: str, root_end: int, section_text: str) -> Edit:
    """Build an Edit that appends *section_text* as a new docstring section.

    *section_text* should contain the fully-indented section (header + entries)
    joined by ``\\n``, without any surrounding blank lines.

    For multiline docstrings (where content ends with ``\\n<indent>``) the
    trailing whitespace is replaced so that:

    * There is exactly one blank line before the new section.
    * The closing triple-quote stays at the original indentation column.

    For single-line docstrings *section_text* is simply appended with a
    two-blank-line separator.
    """
    ds_bytes = ds_text.encode("utf-8")
    last_nl = ds_bytes.rfind(b"\n")
    if last_nl != -1 and not ds_bytes[last_nl + 1 :].strip():
        trailing = ds_bytes[last_nl + 1 :].decode("utf-8")
        return Edit(
            start=last_nl + 1,
            end=root_end,
            new_text=f"\n{section_text}\n{trailing}",
        )
    # Single-line or no trailing whitespace — detect indent from section_text itself
    n = len(section_text) - len(section_text.lstrip(" \t"))
    indent = section_text[:n]
    return Edit(
        start=root_end,
        end=root_end,
        new_text=f"\n\n{section_text}\n{indent}",
    )


def apply_edits(source: str, edits: Iterable[Edit]) -> str:
    """Apply Edits to a docstring, in reverse-offset order.

    Edit offsets are UTF-8 byte positions (as returned by pydocstring-rs).
    """
    sorted_edits: Final[list[Edit]] = sorted(edits, key=lambda e: e.start, reverse=True)
    # Validate no overlaps
    for prev, curr in pairwise(sorted_edits):
        if curr.end > prev.start:
            msg = f"Overlapping edits: [{curr.start}:{curr.end}] and [{prev.start}:{prev.end}]"
            raise ValueError(msg)
    buf: bytes = source.encode("utf-8")
    for edit in sorted_edits:
        buf = buf[: edit.start] + edit.new_text.encode("utf-8") + buf[edit.end :]
    return buf.decode("utf-8")
