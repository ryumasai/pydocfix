"""Linting rules for docstrings."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydocfix.config import Config

from pydocfix.edits import (
    apply_edits,
    delete_range,
    insert_at,
    replace_token,
)
from pydocfix.models import (
    Applicability,
    Diagnostic,
    Edit,
    Fix,
    Offset,
    Range,
    Severity,
)
from pydocfix.plugin_loader import (
    discover_rules_in_module,
    discover_rules_in_package,
    discover_rules_in_path,
    load_plugin_rules,
)
from pydocfix.registry import (
    RuleRegistry,
    _matches_any,
    effective_applicability,
    is_applicable,
)
from pydocfix.rules._base import ActivationCondition, BaseRule, DiagnoseContext, DocstringLocation
from pydocfix.rules._helpers import (
    build_section_stub,
    delete_entry_fix,
    delete_section_fix,
    detect_docstring_style,
    find_section,
    has_section,
)

# --- Docstring-level rules ---
from pydocfix.rules.doc.doc001 import DOC001
from pydocfix.rules.doc.doc002 import DOC002
from pydocfix.rules.doc.doc003 import DOC003

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
from pydocfix.rules.prm.prm106 import PRM106
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
from pydocfix.rules.rtn.rtn106 import RTN106

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
from pydocfix.rules.yld.yld106 import YLD106

__all__ = [
    "Applicability",
    "BaseRule",
    # **** RULES ****
    # sum
    "SUM001",
    "SUM002",
    # doc
    "DOC001",
    "DOC002",
    "DOC003",
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
    "PRM106",
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
    "RTN106",
    # yld
    "YLD001",
    "YLD002",
    "YLD003",
    "YLD101",
    "YLD102",
    "YLD103",
    "YLD104",
    "YLD105",
    "YLD106",
    # **** FRAMEWORK ****
    "ActivationCondition",
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
    "effective_applicability",
    "is_applicable",
    "replace_token",
    # **** HELPERS ****
    "build_section_stub",
    "delete_entry_fix",
    "delete_section_fix",
    "detect_docstring_style",
    "find_section",
    "has_section",
    # **** PLUGIN SYSTEM ****
    "discover_rules_in_module",
    "discover_rules_in_package",
    "discover_rules_in_path",
    "load_plugin_rules",
]

_BUILTIN_RULES: list[type[BaseRule]] = [
    SUM001,
    SUM002,
    DOC001,
    DOC002,
    DOC003,
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
    PRM106,
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
    RTN106,
    YLD001,
    YLD002,
    YLD003,
    YLD101,
    YLD102,
    YLD103,
    YLD104,
    YLD105,
    YLD106,
]


def _check_activation(rule: BaseRule, config: Config | None) -> bool:
    """Return True if *rule*'s activation condition is satisfied (or absent)."""
    cond = rule.activation_condition
    if cond is None:
        return True
    actual = getattr(config, cond.attr, None) if config else None
    return actual in cond.values


def _resolve_conflicts(candidates: list[BaseRule], config: Config | None) -> list[BaseRule]:
    """Remove rules that lose their conflict due to unmet activation conditions.

    A rule declares its conflicts via ``conflicts_with`` (a set of rule codes).
    When a conflicting counterpart is also present in *candidates*, the rule is
    kept only if its ``activation_condition`` is satisfied.  When only one side
    of a conflict is selected (the counterpart is absent), the rule is kept
    unconditionally — the activation condition is only used as a tie-breaker.
    """
    candidate_codes: frozenset[str] = frozenset(r.code for r in candidates)
    result: list[BaseRule] = []
    for rule in candidates:
        active_conflicts = rule.conflicts_with & candidate_codes
        if not active_conflicts:
            # No active conflict — keep unconditionally.
            result.append(rule)
        elif _check_activation(rule, config):
            # In conflict and activation condition met — keep.
            result.append(rule)
        else:
            cond = rule.activation_condition
            if cond is None:  # pragma: no cover  # guaranteed by _check_activation logic
                continue
            allowed = ", ".join(f"'{v}'" for v in sorted(cond.values))
            logging.getLogger(__name__).warning(
                "%s conflicts with [%s] and '%s' is not in {%s}; %s excluded.",
                rule.code,
                ", ".join(sorted(active_conflicts)),
                cond.attr,
                allowed,
                rule.code,
            )
    return result


def build_registry(
    ignore: list[str] | None = None,
    select: list[str] | None = None,
    config: Config | None = None,
    plugin_rules: list[type[BaseRule]] | None = None,
) -> RuleRegistry:
    """Create a registry populated with built-in rules and optional plugins.

    Args:
        ignore: List of rule codes to ignore (supports prefixes).
        select: List of rule codes to select (supports prefixes).
        config: Configuration object for rule activation.
        plugin_rules: Additional rule classes from plugins.

    Returns:
        A RuleRegistry with all applicable rules registered.

    """
    ignored: frozenset[str] = frozenset(ignore or [])
    selected: frozenset[str] = frozenset(select or [])
    select_all: bool = "ALL" in selected
    has_select: bool = bool(selected)

    # Combine built-in and plugin rules
    all_rule_classes = list(_BUILTIN_RULES)
    if plugin_rules:
        all_rule_classes.extend(plugin_rules)

    # Step 1: collect candidates according to select/ignore/default logic.
    # Keep the first selected rule per code to avoid mixed duplicate behavior
    # between the code map and kind-dispatch lists.
    candidates_by_code: dict[str, BaseRule] = {}
    for cls in all_rule_classes:
        instance = cls(config)
        if _matches_any(instance.code, ignored):
            continue
        if (
            select_all
            or (has_select and _matches_any(instance.code, selected))
            or (not has_select and instance.enabled_by_default)
        ):
            if instance.code in candidates_by_code:
                kept = candidates_by_code[instance.code]
                logging.getLogger(__name__).warning(
                    "duplicate rule code '%s': keeping %s.%s, ignoring %s.%s",
                    instance.code,
                    kept.__class__.__module__,
                    kept.__class__.__name__,
                    instance.__class__.__module__,
                    instance.__class__.__name__,
                )
                continue
            candidates_by_code[instance.code] = instance

    candidates: list[BaseRule] = list(candidates_by_code.values())

    # Step 2: resolve any mutual-exclusion conflicts among candidates.
    resolved = _resolve_conflicts(candidates, config)

    # Step 3: register survivors.
    registry = RuleRegistry()
    for instance in resolved:
        registry.register(instance)
    return registry
