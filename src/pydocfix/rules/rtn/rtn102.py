"""Rule RTN102 - Return type not in docstring or signature."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule


@rule("RTN102", targets=FunctionCtx, cst_types=(GoogleReturn, NumPyReturns))
def rtn102(node: GoogleReturn | NumPyReturns, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Return type not specified in either docstring or signature."""
    cst_node = node

    ret_type_token = cst_node.return_type
    if ret_type_token is not None and ret_type_token.text.strip():
        return  # has type in docstring

    func = ctx.parent
    if func.returns is not None:
        return  # has type in signature

    yield make_diagnostic("RTN102", ctx, "Return type not in docstring or signature.", target=cst_node)
