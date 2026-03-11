"""Source file checker — orchestrates parsing and diagnosis."""

from __future__ import annotations

import ast
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Final

import pydocstring
from pydocstring import SyntaxKind

from pydocfix.rules import BaseRule, DiagnoseContext, Diagnostic, Range


def _extract_docstrings(source: str, filepath: Path) -> Iterator[tuple[str, ast.AST, ast.stmt]]:
    """Yield (docstring, parent_node, ds_stmt) for every docstring in source."""
    tree = ast.parse(source, filename=str(filepath))
    for node in ast.walk(tree):
        try:
            ds = ast.get_docstring(node, clean=False)  # type: ignore
            if ds is not None:
                ds_stmt = node.body[0]  # type: ignore
                yield ds, node, ds_stmt
        except TypeError:
            continue  # node has no body, skip


_PREFIX_QUOTE_RE: Final = re.compile(r'([rRuUfFbB]{0,2})("""|\'\'\'\'|"|\')')


def _content_start(lines: list[str], ds_stmt: ast.stmt) -> tuple[int, int]:
    """Return (line, col) where the docstring content begins (after opening quotes).

    line is 1-based, col is 0-based.
    """
    line_text = lines[ds_stmt.lineno - 1]
    m = _PREFIX_QUOTE_RE.match(line_text, pos=ds_stmt.col_offset)
    assert m is not None
    return ds_stmt.lineno, m.end()


def build_kind_map(rules: list[BaseRule]) -> dict[SyntaxKind, list[BaseRule]]:
    """Build kind → rules dispatch map (call once, reuse across files)."""
    kind_map: dict[SyntaxKind, list[BaseRule]] = {}
    for rule in rules:
        for kind in rule.target_kinds:
            kind_map.setdefault(kind, []).append(rule)
    return kind_map


def diagnose_file(filepath: Path, kind_map: dict[SyntaxKind, list[BaseRule]]) -> list[Diagnostic]:
    """Run all rules against every docstring in a file (single pass)."""
    source = filepath.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    diagnostics: list[Diagnostic] = []

    for ds_text, ast_node, ds_stmt in _extract_docstrings(source, filepath):
        style = pydocstring.detect_style(ds_text)
        parsed = (
            pydocstring.parse_numpy(ds_text) if style == pydocstring.Style.NUMPY else pydocstring.parse_google(ds_text)
        )
        model = parsed.to_model()

        ds_range = Range(
            start_line=ds_stmt.lineno,
            start_col=ds_stmt.col_offset,
            end_line=getattr(ds_stmt, "end_lineno", ds_stmt.lineno),
            end_col=getattr(ds_stmt, "end_col_offset", ds_stmt.col_offset),
        )

        # Determine where the docstring content starts (after opening triple-quote).
        content_line, content_col = _content_start(lines, ds_stmt)

        # Walk the CST and dispatch to matching rules
        for cst_node in pydocstring.walk(parsed.node):
            matching_rules = kind_map.get(cst_node.kind, [])
            if not matching_rules:
                continue
            ctx = DiagnoseContext(
                filepath=filepath,
                docstring_source=ds_text,
                docstring_model=model,
                cst=parsed,
                cst_node=cst_node,
                ast_node=ast_node,
                range=ds_range,
                indent=ds_stmt.col_offset,
                content_line=content_line,
                content_col=content_col,
            )
            for rule in matching_rules:
                diag = rule.diagnose(ctx)
                if diag is not None:
                    diagnostics.append(diag)

    return diagnostics
