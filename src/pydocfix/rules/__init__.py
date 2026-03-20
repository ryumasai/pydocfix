"""Linting rules for docstrings."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydocfix.config import Config

from pydocfix.rules._base import (
    Applicability,
    BaseRule,
    DiagnoseContext,
    Diagnostic,
    DocstringLocation,
    Edit,
    Fix,
    Offset,
    Range,
    RuleRegistry,
    Severity,
    apply_edits,
    delete_range,
    insert_at,
    is_applicable,
    replace_token,
)
from pydocfix.rules.d200 import D200
from pydocfix.rules.d401 import D401
from pydocfix.rules.d402 import D402
from pydocfix.rules.d403 import D403
from pydocfix.rules.d404 import D404
from pydocfix.rules.d405 import D405
from pydocfix.rules.d406 import D406
from pydocfix.rules.d407 import D407
from pydocfix.rules.d408 import D408
from pydocfix.rules.d409 import D409

__all__ = [
    "Applicability",
    "BaseRule",
    "D200",
    "D401",
    "D402",
    "D403",
    "D404",
    "D405",
    "D406",
    "D407",
    "D408",
    "D409",
    "DiagnoseContext",
    "Diagnostic",
    "DocstringLocation",
    "Edit",
    "Fix",
    "Offset",
    "Range",
    "RuleRegistry",
    "Severity",
    "apply_edits",
    "build_registry",
    "delete_range",
    "insert_at",
    "is_applicable",
    "replace_token",
]

_BUILTIN_RULES: list[type[BaseRule]] = [
    D200,
    D401,
    D402,
    D403,
    D404,
    D405,
    D406,
    D407,
    D408,
    D409,
]


def build_registry(
    ignore: list[str] | None = None,
    select: list[str] | None = None,
    config: Config | None = None,
) -> RuleRegistry:
    """Create a registry populated with built-in rules.

    Args:
        ignore: Rule codes to exclude (e.g. ``["D200", "D401"]``).
        select: Rule codes to explicitly enable. ``["ALL"]`` enables every rule
            including those with ``enabled_by_default = False``.  When empty,
            only rules whose ``enabled_by_default`` is ``True`` are active.
        config: Resolved configuration passed to each rule instance.
    """
    ignored: frozenset[str] = frozenset(ignore or [])
    selected: frozenset[str] = frozenset(select or [])
    select_all: bool = "ALL" in selected
    has_select: bool = bool(selected)
    registry = RuleRegistry()
    for cls in _BUILTIN_RULES:
        instance = cls(config)
        if instance.code in ignored:
            continue
        if select_all:
            registry.register(instance)
        elif has_select:
            if instance.code in selected:
                registry.register(instance)
        elif instance.enabled_by_default:
            registry.register(instance)
    return registry
