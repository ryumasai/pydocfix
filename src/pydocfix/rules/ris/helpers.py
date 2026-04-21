"""Shared helpers for raises-related rules."""

from __future__ import annotations

import ast

from pydocstring import (
    GoogleSection,
    GoogleSectionKind,
    NumPySection,
    NumPySectionKind,
    Visitor,
)

_RAISES_SECTION_NAMES = frozenset({"Raises", "Raise"})


def is_raises_section(section) -> bool:
    """Return True if *section* is a Raises section."""
    if isinstance(section, GoogleSection):
        return section.section_kind == GoogleSectionKind.RAISES
    if isinstance(section, NumPySection):
        return section.section_kind == NumPySectionKind.RAISES
    return False


def get_docstring_exception_names(parsed, section) -> list[str]:
    """Return bare exception names documented in a Raises section.

    Uses Visitor walk to find GoogleException/NumPyException nodes within the
    section range.
    """
    names: list[str] = []
    sec_start = section.range.start
    sec_end = section.range.end

    class _Collector(Visitor):
        def enter_google_exception(self, node, ctx):
            if sec_start <= node.range.start < sec_end and node.type:
                names.append(_bare_exc_name(node.type.text))

        def enter_numpy_exception(self, node, ctx):
            if sec_start <= node.range.start < sec_end and node.type:
                names.append(_bare_exc_name(node.type.text))

    import pydocstring

    pydocstring.walk(parsed, _Collector())
    return names


def _bare_exc_name(name: str) -> str:
    """Return the unqualified part of an exception name (``a.b.Exc`` -> ``Exc``)."""
    return name.rsplit(".", 1)[-1]


class _RaiseVisitor(ast.NodeVisitor):
    """Collect exception class names raised directly in a function body."""

    def __init__(self) -> None:
        self.raised: list[str] = []

    def visit_Raise(self, node: ast.Raise) -> None:
        if node.exc is None:
            return  # bare re-raise — handled by visit_Try
        exc = node.exc
        if isinstance(exc, ast.Call):
            exc = exc.func
        if isinstance(exc, ast.Name):
            self.raised.append(exc.id)
        elif isinstance(exc, ast.Attribute):
            self.raised.append(exc.attr)

    def visit_Try(self, node: ast.Try) -> None:
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)
        for stmt in node.finalbody:
            self.visit(stmt)
        for handler in node.handlers:
            if handler.type is not None:
                has_bare = any(isinstance(n, ast.Raise) and n.exc is None for n in ast.walk(handler))
                if has_bare:
                    exc = handler.type
                    if isinstance(exc, ast.Name):
                        self.raised.append(exc.id)
                    elif isinstance(exc, ast.Attribute):
                        self.raised.append(exc.attr)
            for stmt in handler.body:
                self.visit(stmt)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        pass

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        pass

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        pass


def get_raised_exceptions(func: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Return determinable exception names raised in the function body."""
    visitor = _RaiseVisitor()
    for stmt in func.body:
        visitor.visit(stmt)
    return visitor.raised
