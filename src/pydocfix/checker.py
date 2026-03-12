"""Source file checker — orchestrates parsing and diagnosis."""

from __future__ import annotations

import ast
import logging
import re
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Final, NamedTuple

import pydocstring
from pydocstring import Style, SyntaxKind

from pydocfix.rules import BaseRule, DiagnoseContext, Diagnostic, Offset

logger = logging.getLogger(__name__)


class _DocstringInfo(NamedTuple):
    """Extracted info about a docstring from source."""

    text: str
    parent_node: ast.AST
    stmt: ast.stmt


def _extract_docstrings(source: str, filepath: Path) -> Iterator[_DocstringInfo]:
    """Yield :class:`_DocstringInfo` for every docstring in *source*."""
    try:
        tree: Final = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        logger.warning(f"{filepath}: could not parse (syntax error), skipping")
        return

    for node in ast.walk(tree):
        try:
            docstr: Final = ast.get_docstring(node, clean=False)  # type: ignore
        except TypeError:
            continue  # node cannot have a docstring

        if docstr is None:
            continue  # node has no docstring

        yield _DocstringInfo(
            docstr,
            node,
            node.body[0],  # type: ignore
        )


_REGEX_OPENING_QUOTES: Final = re.compile(r'([rRuUfFbB]{0,2})("""|\'\'\'\'|"|\')')


def _docstring_text_offset(docstr_stmt: ast.stmt, lines: Sequence[str]) -> Offset | None:
    """Return the position where the docstring content begins (after opening quotes)."""
    line: Final = lines[docstr_stmt.lineno - 1]
    matched: Final = _REGEX_OPENING_QUOTES.match(line, pos=docstr_stmt.col_offset)
    if matched is None:
        logger.warning("could not locate opening quote at line %d", docstr_stmt.lineno)
        return None
    return Offset(docstr_stmt.lineno, matched.end())


def build_rules_map(rules: Iterable[BaseRule]) -> dict[SyntaxKind, list[BaseRule]]:
    """Build cst->rules dispatch map."""
    kind_map: dict[SyntaxKind, list[BaseRule]] = {}
    for rule in rules:
        for kind in rule.target_kinds:
            kind_map.setdefault(kind, []).append(rule)
    return kind_map


def diagnose_file(filepath: Path, kind_map: dict[SyntaxKind, list[BaseRule]]) -> list[Diagnostic]:
    """Run all rules against every docstring in a file (single pass)."""
    source: Final = filepath.read_text(encoding="utf-8")
    lines: Final = source.splitlines(keepends=True)
    diagnostics: list[Diagnostic] = []

    for docstr_text, parent_node, docstr_stmt in _extract_docstrings(source, filepath):
        style = pydocstring.detect_style(docstr_text)
        parsed = pydocstring.parse_numpy(docstr_text) if style == Style.NUMPY else pydocstring.parse_google(docstr_text)

        # Determine where the docstring content starts (after opening triple-quote).
        docstring_text_offset = _docstring_text_offset(docstr_stmt, lines)
        if docstring_text_offset is None:
            continue

        # Walk the CST and dispatch to matching rules
        for cst in pydocstring.walk(parsed.node):
            matching_rules = kind_map.get(cst.kind, [])
            if not matching_rules:
                continue
            ctx = DiagnoseContext(
                filepath=filepath,
                docstring_text=docstr_text,
                docstring_cst=parsed,
                target_cst=cst,
                parent_ast=parent_node,
                docstring_stmt=docstr_stmt,
                docstring_text_offset=docstring_text_offset,
            )
            for rule in matching_rules:
                diag = rule.diagnose(ctx)
                if diag is not None:
                    diagnostics.append(diag)

    return diagnostics
