"""PLUGIN001: minimal plugin rule for path-based discovery tests."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import BaseCtx, FunctionCtx, ModuleCtx, rule


@rule(
    "PLUGIN001",
    targets=(FunctionCtx, ModuleCtx),
    cst_types=(GoogleDocstring, NumPyDocstring, PlainDocstring),
)
def plugin001(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: BaseCtx) -> Iterator[Diagnostic]:
    """Minimal plugin rule; always a no-op."""
    return iter(())
