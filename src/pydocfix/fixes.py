"""Fix and Edit factory utilities for plugin authors."""

from __future__ import annotations

from pydocstring import Token

from pydocfix.diagnostics import Applicability, Edit, Fix


def safe_fix(edits: list[Edit]) -> Fix:
    """Create a safe Fix from a list of Edits."""
    return Fix(edits=edits, applicability=Applicability.SAFE)


def unsafe_fix(edits: list[Edit]) -> Fix:
    """Create an unsafe Fix from a list of Edits."""
    return Fix(edits=edits, applicability=Applicability.UNSAFE)


def replace_token(token: Token, new_text: str) -> Edit:
    """Replace a token's entire text."""
    return Edit(start=token.range.start, end=token.range.end, new_text=new_text)


def insert_at(offset: int, text: str) -> Edit:
    """Insert text at a byte offset (no deletion)."""
    return Edit(start=offset, end=offset, new_text=text)


def delete_range(start: int, end: int) -> Edit:
    """Delete a byte range."""
    return Edit(start=start, end=end, new_text="")


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
