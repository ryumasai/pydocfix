"""Shared helpers for return-related rules."""

from __future__ import annotations

import ast

from pydocstring import (
    GoogleSection,
    GoogleSectionKind,
    NumPySection,
    NumPySectionKind,
)


def has_return_annotation(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True if the function has a meaningful (non-None) return type annotation."""
    if func.returns is None:
        return False
    if isinstance(func.returns, ast.Constant) and func.returns.value is None:
        return False
    return ast.unparse(func.returns) not in ("None",)


def returns_a_value(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True if the function has at least one ``return <expr>`` statement.

    Bare ``return`` and ``return None`` are not considered returning a value.
    Only the top-level function body is inspected (nested functions/classes are
    skipped so they don't influence the result).
    """

    class _Visitor(ast.NodeVisitor):
        found = False

        def visit_Return(self, node: ast.Return) -> None:
            if node.value is not None and not (isinstance(node.value, ast.Constant) and node.value.value is None):
                self.found = True

        # Do not descend into nested scopes
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            pass

        visit_AsyncFunctionDef = visit_FunctionDef
        visit_ClassDef = visit_FunctionDef

    v = _Visitor()
    for child in func.body:
        v.visit(child)
    return v.found


def is_returns_section(section) -> bool:
    """Return True if *section* is a Returns section."""
    if isinstance(section, GoogleSection):
        return section.section_kind == GoogleSectionKind.RETURNS
    if isinstance(section, NumPySection):
        return section.section_kind == NumPySectionKind.RETURNS
    return False
