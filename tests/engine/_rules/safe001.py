"""SAFE001: synthetic rule that detects and safely fixes VIOLATION(SAFE001) in summary."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.diagnostics import Applicability, Diagnostic, Fix
from pydocfix.fixes import replace_token
from pydocfix.rules._base import BaseCtx, ClassCtx, FunctionCtx, ModuleCtx, make_diagnostic, rule

_VIOLATION = "VIOLATION(SAFE001)"
_FIXED = "FIXED(SAFE001)."


@rule(
    "SAFE001",
    ctx_types=frozenset({FunctionCtx, ClassCtx, ModuleCtx}),
    cst_types=frozenset({GoogleDocstring, NumPyDocstring, PlainDocstring}),
)
def safe001(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: BaseCtx) -> Iterator[Diagnostic]:
    """Detects VIOLATION(SAFE001) in docstring summary and fixes it safely."""
    if node.summary is None or _VIOLATION not in node.summary.text:
        return
    fix = Fix(
        edits=[replace_token(node.summary, _FIXED)],
        applicability=Applicability.SAFE,
    )
    yield make_diagnostic("SAFE001", ctx, f"Summary contains {_VIOLATION!r}", fix=fix, target=node.summary)
