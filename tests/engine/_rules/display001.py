"""DISPLAY001: synthetic rule with DISPLAY_ONLY fix — never applied by the fixer."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.diagnostics import Applicability, Diagnostic, Fix
from pydocfix.fixes import replace_token
from pydocfix.rules._base import BaseCtx, ClassCtx, FunctionCtx, ModuleCtx, make_diagnostic, rule

_VIOLATION = "VIOLATION(DISPLAY001)"


@rule(
    "DISPLAY001",
    ctx_types=frozenset({FunctionCtx, ClassCtx, ModuleCtx}),
    cst_types=frozenset({GoogleDocstring, NumPyDocstring, PlainDocstring}),
)
def display001(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: BaseCtx) -> Iterator[Diagnostic]:
    """Detects VIOLATION(DISPLAY001) and proposes a DISPLAY_ONLY fix (never applied)."""
    if node.summary is None or _VIOLATION not in node.summary.text:
        return
    fix = Fix(
        edits=[replace_token(node.summary, "FIXED(DISPLAY001).")],
        applicability=Applicability.DISPLAY_ONLY,
    )
    yield make_diagnostic("DISPLAY001", ctx, f"Summary contains {_VIOLATION!r}", fix=fix, target=node.summary)
