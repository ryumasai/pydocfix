"""Linting rules for docstrings."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydocfix.config import Config

from pydocfix.diagnostics import (
    Applicability,
    Diagnostic,
    Edit,
    Fix,
    Offset,
    Range,
)
from pydocfix.engine.plugin_loader import (
    discover_rules_in_module,
    discover_rules_in_package,
    discover_rules_in_path,
    load_plugin_rules,
)
from pydocfix.engine.registry import (
    RuleRegistry,
    _matches_any,
    effective_applicability,
    is_applicable,
)
from pydocfix.fixes import (
    delete_range,
    insert_at,
    replace_token,
    safe_fix,
    unsafe_fix,
)
from pydocfix.rules._base import (
    ActivationCondition,
    BaseCtx,
    ClassCtx,
    DocstringLocation,
    FunctionCtx,
    ModuleCtx,
    RuleFn,
    make_diagnostic,
    rule,
)

# --- Class rules ---
from pydocfix.rules.cls.cls001 import cls001
from pydocfix.rules.cls.cls101 import cls101
from pydocfix.rules.cls.cls102 import cls102
from pydocfix.rules.cls.cls103 import cls103
from pydocfix.rules.cls.cls104 import cls104
from pydocfix.rules.cls.cls105 import cls105
from pydocfix.rules.cls.cls106 import cls106
from pydocfix.rules.cls.cls201 import cls201
from pydocfix.rules.cls.cls202 import cls202
from pydocfix.rules.cls.cls203 import cls203
from pydocfix.rules.cls.cls204 import cls204
from pydocfix.rules.cls.cls205 import cls205
from pydocfix.rules.cls.cls206 import cls206

# --- Docstring-level rules ---
from pydocfix.rules.doc.doc001 import doc001
from pydocfix.rules.doc.doc002 import doc002
from pydocfix.rules.doc.doc003 import doc003
from pydocfix.rules.helpers import (
    build_section_stub,
    delete_entry_fix,
    delete_section_fix,
    detect_docstring_style,
    detect_section_indent,
    find_section,
    has_section,
    normalize_optional,
)

# --- Parameter rules ---
from pydocfix.rules.prm.prm001 import prm001
from pydocfix.rules.prm.prm002 import prm002
from pydocfix.rules.prm.prm003 import prm003
from pydocfix.rules.prm.prm004 import prm004
from pydocfix.rules.prm.prm005 import prm005
from pydocfix.rules.prm.prm006 import prm006
from pydocfix.rules.prm.prm007 import prm007
from pydocfix.rules.prm.prm008 import prm008
from pydocfix.rules.prm.prm009 import prm009
from pydocfix.rules.prm.prm101 import prm101
from pydocfix.rules.prm.prm102 import prm102
from pydocfix.rules.prm.prm103 import prm103
from pydocfix.rules.prm.prm104 import prm104
from pydocfix.rules.prm.prm105 import prm105
from pydocfix.rules.prm.prm106 import prm106
from pydocfix.rules.prm.prm201 import prm201
from pydocfix.rules.prm.prm202 import prm202

# --- Raises rules ---
from pydocfix.rules.ris.ris001 import ris001
from pydocfix.rules.ris.ris002 import ris002
from pydocfix.rules.ris.ris003 import ris003
from pydocfix.rules.ris.ris004 import ris004
from pydocfix.rules.ris.ris005 import ris005

# --- Return rules ---
from pydocfix.rules.rtn.rtn001 import rtn001
from pydocfix.rules.rtn.rtn002 import rtn002
from pydocfix.rules.rtn.rtn003 import rtn003
from pydocfix.rules.rtn.rtn101 import rtn101
from pydocfix.rules.rtn.rtn102 import rtn102
from pydocfix.rules.rtn.rtn103 import rtn103
from pydocfix.rules.rtn.rtn104 import rtn104
from pydocfix.rules.rtn.rtn105 import rtn105
from pydocfix.rules.rtn.rtn106 import rtn106

# --- Summary rules ---
from pydocfix.rules.sum.sum001 import sum001
from pydocfix.rules.sum.sum002 import sum002

# --- Yield rules ---
from pydocfix.rules.yld.yld001 import yld001
from pydocfix.rules.yld.yld002 import yld002
from pydocfix.rules.yld.yld003 import yld003
from pydocfix.rules.yld.yld101 import yld101
from pydocfix.rules.yld.yld102 import yld102
from pydocfix.rules.yld.yld103 import yld103
from pydocfix.rules.yld.yld104 import yld104
from pydocfix.rules.yld.yld105 import yld105
from pydocfix.rules.yld.yld106 import yld106

__all__ = [
    "Applicability",
    # **** FRAMEWORK ****
    "ActivationCondition",
    "BaseCtx",
    "ClassCtx",
    "Diagnostic",
    "DocstringLocation",
    "Edit",
    "Fix",
    "FunctionCtx",
    "ModuleCtx",
    "Offset",
    "Range",
    "RuleFn",
    "RuleRegistry",
    "build_registry",
    "delete_range",
    "insert_at",
    "effective_applicability",
    "is_applicable",
    "make_diagnostic",
    "replace_token",
    "rule",
    "safe_fix",
    "unsafe_fix",
    # **** HELPERS ****
    "build_section_stub",
    "delete_entry_fix",
    "delete_section_fix",
    "detect_docstring_style",
    "detect_section_indent",
    "find_section",
    "has_section",
    "normalize_optional",
    # **** PLUGIN SYSTEM ****
    "discover_rules_in_module",
    "discover_rules_in_package",
    "discover_rules_in_path",
    "load_plugin_rules",
]

_BUILTIN_RULES: list[RuleFn] = [
    sum001,
    sum002,
    doc001,
    doc002,
    doc003,
    cls001,
    cls101,
    cls102,
    cls103,
    cls104,
    cls105,
    cls106,
    cls201,
    cls202,
    cls203,
    cls204,
    cls205,
    cls206,
    prm001,
    prm002,
    prm003,
    prm004,
    prm005,
    prm006,
    prm007,
    prm008,
    prm009,
    prm101,
    prm102,
    prm103,
    prm104,
    prm105,
    prm106,
    prm201,
    prm202,
    ris001,
    ris002,
    ris003,
    ris004,
    ris005,
    rtn001,
    rtn002,
    rtn003,
    rtn101,
    rtn102,
    rtn103,
    rtn104,
    rtn105,
    rtn106,
    yld001,
    yld002,
    yld003,
    yld101,
    yld102,
    yld103,
    yld104,
    yld105,
    yld106,
]


def _check_activation(rule_fn: RuleFn, config: Config | None) -> bool:
    """Return True if *rule_fn*'s activation condition is satisfied (or absent)."""
    cond = rule_fn._activation_condition  # type: ignore[attr-defined]
    if cond is None:
        return True
    actual = getattr(config, cond.attr, None) if config else None
    return actual in cond.values


def _resolve_conflicts(candidates: list[RuleFn], config: Config | None) -> list[RuleFn]:
    """Remove rules that lose their conflict due to unmet activation conditions.

    A rule declares its conflicts via ``conflicts_with`` (a set of rule codes).
    When a conflicting counterpart is also present in *candidates*, the rule is
    kept only if its ``activation_condition`` is satisfied.  When only one side
    of a conflict is selected (the counterpart is absent), the rule is kept
    unconditionally — the activation condition is only used as a tie-breaker.
    """
    candidate_codes: frozenset[str] = frozenset(fn._rule_code for fn in candidates)  # type: ignore[attr-defined]
    result: list[RuleFn] = []
    for rule_fn in candidates:
        code = rule_fn._rule_code  # type: ignore[attr-defined]
        active_conflicts = rule_fn._conflicts_with & candidate_codes  # type: ignore[attr-defined]
        if not active_conflicts or _check_activation(rule_fn, config):
            result.append(rule_fn)
        else:
            cond = rule_fn._activation_condition  # type: ignore[attr-defined]
            if cond is None:  # pragma: no cover
                continue
            allowed = ", ".join(f"'{v}'" for v in sorted(cond.values))
            logging.getLogger(__name__).warning(
                "%s conflicts with [%s] and '%s' is not in {%s}; %s excluded.",
                code,
                ", ".join(sorted(active_conflicts)),
                cond.attr,
                allowed,
                code,
            )
    return result


def build_registry(
    ignore: list[str] | None = None,
    select: list[str] | None = None,
    config: Config | None = None,
    plugin_rules: list[RuleFn] | None = None,
) -> RuleRegistry:
    """Create a registry populated with built-in rules and optional plugins.

    Args:
        ignore: List of rule codes to ignore (supports prefixes).
        select: List of rule codes to select (supports prefixes).
        config: Configuration object for rule activation.
        plugin_rules: Additional rule functions from plugins.

    Returns:
        A RuleRegistry with all applicable rules registered.

    """
    ignored: frozenset[str] = frozenset(ignore or [])
    selected: frozenset[str] = frozenset(select or [])
    select_all: bool = "ALL" in selected
    has_select: bool = bool(selected)

    # Combine built-in and plugin rules
    all_rules = list(_BUILTIN_RULES)
    if plugin_rules:
        all_rules.extend(plugin_rules)

    # Step 1: collect candidates according to select/ignore/default logic.
    candidates_by_code: dict[str, RuleFn] = {}
    for rule_fn in all_rules:
        code = rule_fn._rule_code  # type: ignore[attr-defined]
        if _matches_any(code, ignored):
            continue
        enabled = rule_fn._enabled_by_default  # type: ignore[attr-defined]
        if select_all or (has_select and _matches_any(code, selected)) or (not has_select and enabled):
            if code in candidates_by_code:
                kept = candidates_by_code[code]
                logging.getLogger(__name__).warning(
                    "duplicate rule code '%s': keeping %s.%s, ignoring %s.%s",
                    code,
                    kept.__module__,
                    kept.__qualname__,
                    rule_fn.__module__,
                    rule_fn.__qualname__,
                )
                continue
            candidates_by_code[code] = rule_fn

    candidates: list[RuleFn] = list(candidates_by_code.values())

    # Step 2: resolve any mutual-exclusion conflicts among candidates.
    resolved = _resolve_conflicts(candidates, config)

    # Step 3: register survivors.
    registry = RuleRegistry()
    for rule_fn in resolved:
        registry.register(rule_fn)
    return registry
