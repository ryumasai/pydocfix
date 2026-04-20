"""Rule YLD003 - Yields section has no description."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule


@rule("YLD003", targets=FunctionCtx, cst_types=(GoogleYield, NumPyYields))
def yld003(node: GoogleYield | NumPyYields, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Yields section entry has no description."""
    cst_node = node

    desc = cst_node.description
    if desc is not None and desc.text.strip():
        return

    ret_type = cst_node.return_type
    yield make_diagnostic("YLD003", ctx, "Yields section has no description.", target=ret_type or cst_node)
