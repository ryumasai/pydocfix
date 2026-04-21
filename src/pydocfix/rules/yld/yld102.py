"""Rule YLD102 - Yield type not in docstring or signature."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.yld.helpers import get_yield_type


@rule("YLD102", ctx_types=frozenset({FunctionCtx}), cst_types=frozenset({GoogleYield, NumPyYields}))
def yld102(node: GoogleYield | NumPyYields, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Yield type not specified in either docstring or signature."""
    cst_node = node

    ret_type_token = cst_node.return_type
    if ret_type_token is not None and ret_type_token.text.strip():
        return

    if get_yield_type(ctx.parent) is not None:
        return

    yield make_diagnostic("YLD102", ctx, "Yield type not in docstring or signature.", target=cst_node)
