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

# --- Docstring-level rules ---
from pydocfix.rules.doc.doc001 import DOC001

# --- Parameter rules ---
from pydocfix.rules.prm.prm001 import PRM001
from pydocfix.rules.prm.prm002 import PRM002
from pydocfix.rules.prm.prm003 import PRM003
from pydocfix.rules.prm.prm004 import PRM004
from pydocfix.rules.prm.prm005 import PRM005
from pydocfix.rules.prm.prm006 import PRM006
from pydocfix.rules.prm.prm007 import PRM007
from pydocfix.rules.prm.prm008 import PRM008
from pydocfix.rules.prm.prm009 import PRM009
from pydocfix.rules.prm.prm101 import PRM101
from pydocfix.rules.prm.prm102 import PRM102
from pydocfix.rules.prm.prm103 import PRM103
from pydocfix.rules.prm.prm104 import PRM104
from pydocfix.rules.prm.prm105 import PRM105
from pydocfix.rules.prm.prm201 import PRM201
from pydocfix.rules.prm.prm202 import PRM202

# --- Raises rules ---
from pydocfix.rules.ris.ris001 import RIS001
from pydocfix.rules.ris.ris002 import RIS002
from pydocfix.rules.ris.ris003 import RIS003
from pydocfix.rules.ris.ris004 import RIS004
from pydocfix.rules.ris.ris005 import RIS005

# --- Return rules ---
from pydocfix.rules.rtn.rtn001 import RTN001
from pydocfix.rules.rtn.rtn002 import RTN002
from pydocfix.rules.rtn.rtn003 import RTN003
from pydocfix.rules.rtn.rtn101 import RTN101
from pydocfix.rules.rtn.rtn102 import RTN102
from pydocfix.rules.rtn.rtn103 import RTN103
from pydocfix.rules.rtn.rtn104 import RTN104
from pydocfix.rules.rtn.rtn105 import RTN105

# --- Summary rules ---
from pydocfix.rules.sum.sum001 import SUM001
from pydocfix.rules.sum.sum002 import SUM002

# --- Yield rules ---
from pydocfix.rules.yld.yld001 import YLD001
from pydocfix.rules.yld.yld002 import YLD002
from pydocfix.rules.yld.yld003 import YLD003
from pydocfix.rules.yld.yld101 import YLD101
from pydocfix.rules.yld.yld102 import YLD102
from pydocfix.rules.yld.yld103 import YLD103
from pydocfix.rules.yld.yld104 import YLD104
from pydocfix.rules.yld.yld105 import YLD105

__all__ = [
    "Applicability",
    "BaseRule",
    # **** RULES ****
    # sum
    "SUM001",
    "SUM002",
    # doc
    "DOC001",
    # prm
    "PRM001",
    "PRM002",
    "PRM003",
    "PRM004",
    "PRM005",
    "PRM006",
    "PRM007",
    "PRM008",
    "PRM009",
    "PRM101",
    "PRM102",
    "PRM103",
    "PRM104",
    "PRM105",
    "PRM201",
    "PRM202",
    # ris
    "RIS001",
    "RIS002",
    "RIS003",
    "RIS004",
    "RIS005",
    # rtn
    "RTN001",
    "RTN002",
    "RTN003",
    "RTN101",
    "RTN102",
    "RTN103",
    "RTN104",
    "RTN105",
    # yld
    "YLD001",
    "YLD002",
    "YLD003",
    "YLD101",
    "YLD102",
    "YLD103",
    "YLD104",
    "YLD105",
    # **** FRAMEWORK ****
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
    # **** CONSTANTS ****
    "ALL_RULE_CODES",
]

_BUILTIN_RULES: list[type[BaseRule]] = [
    SUM001,
    SUM002,
    DOC001,
    PRM001,
    PRM002,
    PRM003,
    PRM004,
    PRM005,
    PRM006,
    PRM007,
    PRM008,
    PRM009,
    PRM101,
    PRM102,
    PRM103,
    PRM104,
    PRM105,
    PRM201,
    PRM202,
    RIS001,
    RIS002,
    RIS003,
    RIS004,
    RIS005,
    RTN001,
    RTN002,
    RTN003,
    RTN101,
    RTN102,
    RTN103,
    RTN104,
    RTN105,
    YLD001,
    YLD002,
    YLD003,
    YLD101,
    YLD102,
    YLD103,
    YLD104,
    YLD105,
]

ALL_RULE_CODES: frozenset[str] = frozenset(cls.code for cls in _BUILTIN_RULES)


def _matches(code: str, patterns: frozenset[str]) -> bool:
    """Return True if *code* matches any pattern (exact or prefix)."""
    return any(code == p or code.startswith(p) for p in patterns)


def _resolve_conflicts(candidates: list[BaseRule], config: Config | None) -> list[BaseRule]:
    """Remove conflicting rules from *candidates*, keeping only config-matched winners.

    A rule declares its conflicts via ``conflicts_with`` (a set of rule codes).
    When a conflicting counterpart is also present in *candidates*, the rule is
    kept only if its ``requires_config`` condition is satisfied.  When only one
    side of a conflict is selected, it is kept unconditionally.
    """
    candidate_codes: frozenset[str] = frozenset(r.code for r in candidates)
    result: list[BaseRule] = []
    for rule in candidates:
        active_conflicts = rule.conflicts_with & candidate_codes
        if not active_conflicts:
            # No active conflict — keep unconditionally.
            result.append(rule)
        elif rule.requires_config is None:
            # In conflict but no resolution condition declared — keep.
            result.append(rule)
        else:
            actual = getattr(config, rule.requires_config.attr, None) if config else None
            if actual in rule.requires_config.values:
                result.append(rule)
            else:
                import logging

                allowed = ", ".join(f"'{v}'" for v in sorted(rule.requires_config.values))
                logging.getLogger(__name__).warning(
                    "%s conflicts with [%s] and '%s' is not in {%s}; %s excluded.",
                    rule.code,
                    ", ".join(sorted(active_conflicts)),
                    rule.requires_config.attr,
                    allowed,
                    rule.code,
                )
    return result


def build_registry(
    ignore: list[str] | None = None,
    select: list[str] | None = None,
    config: Config | None = None,
) -> RuleRegistry:
    """Create a registry populated with built-in rules."""
    ignored: frozenset[str] = frozenset(ignore or [])
    selected: frozenset[str] = frozenset(select or [])
    select_all: bool = "ALL" in selected
    has_select: bool = bool(selected)

    # Step 1: collect candidates according to select/ignore/default logic.
    candidates: list[BaseRule] = []
    for cls in _BUILTIN_RULES:
        instance = cls(config)
        if _matches(instance.code, ignored):
            continue
        if (
            select_all
            or (has_select and _matches(instance.code, selected))
            or (not has_select and instance.enabled_by_default)
        ):
            candidates.append(instance)

    # Step 2: resolve any mutual-exclusion conflicts among candidates.
    resolved = _resolve_conflicts(candidates, config)

    # Step 3: register survivors.
    registry = RuleRegistry()
    for instance in resolved:
        registry.register(instance)
    return registry
