"""Rule RTN003 - Returns section has no description."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule


@rule("RTN003", targets=FunctionCtx, cst_types=(GoogleReturn, NumPyReturns))
def rtn003(node: GoogleReturn | NumPyReturns, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Returns section entry has no description."""
    cst_node = node

    desc = cst_node.description
    if desc is not None and desc.text.strip():
        return

    ret_type = cst_node.return_type
    yield make_diagnostic("RTN003", ctx, "Returns section has no description.", target=ret_type or cst_node)
