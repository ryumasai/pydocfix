"""Shared helpers for yield-related rules."""

from __future__ import annotations

import ast

from pydocstring import (
    GoogleSection,
    GoogleSectionKind,
    NumPySection,
    NumPySectionKind,
)


def is_yields_section(section) -> bool:
    """Return True if *section* is a Yields section."""
    if isinstance(section, GoogleSection):
        return section.section_kind == GoogleSectionKind.YIELDS
    if isinstance(section, NumPySection):
        return section.section_kind == NumPySectionKind.YIELDS
    return False


class _YieldVisitor(ast.NodeVisitor):
    """Detect yield/yield from at the function body level (not in nested defs)."""

    def __init__(self) -> None:
        self.has_yield = False

    def visit_Yield(self, node: ast.Yield) -> None:
        self.has_yield = True

    def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
        self.has_yield = True

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        pass

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        pass

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        pass


def is_generator_function(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True if the function body contains yield/yield from (not in nested defs)."""
    visitor = _YieldVisitor()
    for stmt in func.body:
        visitor.visit(stmt)
    return visitor.has_yield


def get_yield_type(func: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """Extract yield type from Generator/Iterator/AsyncGenerator return annotation."""
    if func.returns is None:
        return None
    ann = func.returns
    if isinstance(ann, ast.Subscript):
        base = ast.unparse(ann.value)
        base_name = base.rsplit(".", 1)[-1]
        if base_name in ("Generator", "Iterator", "Iterable", "AsyncGenerator", "AsyncIterator", "AsyncIterable"):
            if isinstance(ann.slice, ast.Tuple) and ann.slice.elts:
                return ast.unparse(ann.slice.elts[0])
            else:
                return ast.unparse(ann.slice)
    return None
