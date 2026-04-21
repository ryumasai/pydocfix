"""Shared helpers for class-related rules."""

from __future__ import annotations

import ast

from pydocstring import (
    GoogleSection,
    GoogleSectionKind,
    NumPySection,
    NumPySectionKind,
)


def is_returns_section(section) -> bool:
    """Return True if *section* is a Returns section."""
    if isinstance(section, GoogleSection):
        return section.section_kind == GoogleSectionKind.RETURNS
    if isinstance(section, NumPySection):
        return section.section_kind == NumPySectionKind.RETURNS
    return False


def is_yields_section(section) -> bool:
    """Return True if *section* is a Yields section."""
    if isinstance(section, GoogleSection):
        return section.section_kind == GoogleSectionKind.YIELDS
    if isinstance(section, NumPySection):
        return section.section_kind == NumPySectionKind.YIELDS
    return False


def is_raises_section(section) -> bool:
    """Return True if *section* is a Raises section."""
    if isinstance(section, GoogleSection):
        return section.section_kind == GoogleSectionKind.RAISES
    if isinstance(section, NumPySection):
        return section.section_kind == NumPySectionKind.RAISES
    return False


def is_param_section(section) -> bool:
    """Return True if *section* is an Args/Parameters section."""
    if isinstance(section, GoogleSection):
        return section.section_kind == GoogleSectionKind.ARGS
    if isinstance(section, NumPySection):
        return section.section_kind == NumPySectionKind.PARAMETERS
    return False


def get_init_method(class_def: ast.ClassDef) -> ast.FunctionDef | None:
    """Return the __init__ FunctionDef from a ClassDef, or None if absent."""
    for stmt in class_def.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
            return stmt
    return None
