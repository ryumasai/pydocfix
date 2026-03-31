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
    # yld
    "YLD001",
    "YLD002",
    "YLD003",
    "YLD101",
    "YLD102",
    "YLD103",
    "YLD104",
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
    YLD001,
    YLD002,
    YLD003,
    YLD101,
    YLD102,
    YLD103,
    YLD104,
]


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
