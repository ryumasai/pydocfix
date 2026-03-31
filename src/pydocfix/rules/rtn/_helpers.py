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


def is_returns_section(section) -> bool:
    """Return True if *section* is a Returns section."""
    if isinstance(section, GoogleSection):
        return section.section_kind == GoogleSectionKind.RETURNS
    if isinstance(section, NumPySection):
        return section.section_kind == NumPySectionKind.RETURNS
    return False
