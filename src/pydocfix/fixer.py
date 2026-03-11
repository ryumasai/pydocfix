"""Auto-fix logic for docstring issues."""

from __future__ import annotations

import ast
from pathlib import Path

from pydocfix.checker import _extract_docstrings
from pydocfix.rules import Diagnostic, Edit, apply_edits


def fix_file(
    filepath: Path,
    diagnostics: list[Diagnostic],
) -> str | None:
    """Apply auto-fixes for all fixable diagnostics and return the new source.

    Returns None if no changes were made.
    """
    fixable = [d for d in diagnostics if d.fixable]
    if not fixable:
        return None

    source = filepath.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)

    # Build lookup: docstring_line -> list of Edits
    edits_by_line: dict[int, list[Edit]] = {}
    for d in fixable:
        assert d.fix is not None
        edits_by_line.setdefault(d.docstring_line, []).extend(d.fix.edits)

    # Collect (file_start, file_end, new_docstring) per docstring
    file_edits: list[tuple[int, int, str]] = []

    for ds, _ast_node, ds_stmt in _extract_docstrings(source, filepath):
        text_edits = edits_by_line.get(ds_stmt.lineno, [])
        if not text_edits:
            continue

        raw = ds
        new_raw = apply_edits(raw, text_edits)

        assert isinstance(ds_stmt, ast.Expr)
        start, end = _find_docstring_range(lines, ds_stmt)
        original = source[start:end]
        quote = original[:3]
        file_edits.append((start, end, quote + new_raw + quote))

    if not file_edits:
        return None

    # Apply file-level edits bottom-up to keep offsets valid
    file_edits.sort(key=lambda e: e[0], reverse=True)
    new_source = source
    for start, end, replacement in file_edits:
        new_source = new_source[:start] + replacement + new_source[end:]

    return new_source


def _find_docstring_range(lines: list[str], ds_stmt: ast.Expr) -> tuple[int, int]:
    """Return (start, end) byte offsets of the docstring in source."""
    # ast line numbers are 1-based
    start_offset = sum(len(line) for line in lines[: ds_stmt.lineno - 1])
    start = start_offset + ds_stmt.col_offset
    end_offset = sum(len(line) for line in lines[: ds_stmt.end_lineno - 1])
    end = end_offset + ds_stmt.end_col_offset
    return start, end
