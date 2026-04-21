"""ALWAYS001: synthetic rule that fires on every docstring (no fix)."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import BaseCtx, ClassCtx, FunctionCtx, ModuleCtx, make_diagnostic, rule


@rule(
    "ALWAYS001",
    ctx_types=frozenset({FunctionCtx, ClassCtx, ModuleCtx}),
    cst_types=frozenset({GoogleDocstring, NumPyDocstring, PlainDocstring}),
)
def always001(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: BaseCtx) -> Iterator[Diagnostic]:
    """Fires a diagnostic on every docstring regardless of content."""
    yield make_diagnostic("ALWAYS001", ctx, "Always fires on every docstring", target=node)
