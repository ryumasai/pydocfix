"""PLUGIN003 (modules side): wins in the plugin_modules vs plugin_paths precedence test."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import BaseCtx, FunctionCtx, ModuleCtx, rule


@rule(
    "PLUGIN003",
    ctx_types=frozenset({FunctionCtx, ModuleCtx}),
    cst_types=frozenset({GoogleDocstring, NumPyDocstring, PlainDocstring}),
)
def plugin003(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: BaseCtx) -> Iterator[Diagnostic]:
    """PLUGIN003 loaded via plugin_modules (higher precedence)."""
    return iter(())
