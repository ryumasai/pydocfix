"""SAFE000: synthetic rule that also fixes VIOLATION(SAFE001) — used to test overlapping fix skipping."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.diagnostics import Applicability, Diagnostic, Fix
from pydocfix.fixes import replace_token
from pydocfix.rules._base import BaseCtx, ClassCtx, FunctionCtx, ModuleCtx, make_diagnostic, rule

_VIOLATION = "VIOLATION(SAFE001)"
_FIXED = "FIXED(SAFE000)."


@rule(
    "SAFE000", targets=(FunctionCtx, ClassCtx, ModuleCtx), cst_types=(GoogleDocstring, NumPyDocstring, PlainDocstring)
)
def safe000(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: BaseCtx) -> Iterator[Diagnostic]:
    """Detects VIOLATION(SAFE001) and proposes a competing fix over the same token."""
    if node.summary is None or _VIOLATION not in node.summary.text:
        return
    fix = Fix(
        edits=[replace_token(node.summary, _FIXED)],
        applicability=Applicability.SAFE,
    )
    yield make_diagnostic("SAFE000", ctx, f"Summary contains {_VIOLATION!r}", fix=fix, target=node.summary)
