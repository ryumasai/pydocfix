"""PLUGIN002: underscore-prefixed file — must be skipped by discover_rules_in_path."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import BaseCtx, FunctionCtx, ModuleCtx, rule


@rule(
    "PLUGIN002",
    targets=(FunctionCtx, ModuleCtx),
    cst_types=(GoogleDocstring, NumPyDocstring, PlainDocstring),
)
def plugin002(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: BaseCtx) -> Iterator[Diagnostic]:
    """Plugin rule in a _-prefixed file; should never be discovered via path."""
    return iter(())
