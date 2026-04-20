"""Rule RIS003 - Raises entry has no description."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleException, NumPyException

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule


@rule("RIS003", targets=FunctionCtx, cst_types=(GoogleException, NumPyException))
def ris003(node: GoogleException | NumPyException, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Raises entry has no description."""
    cst_node = node

    desc = cst_node.description
    if desc is not None and desc.text.strip():
        return

    type_token = cst_node.type
    yield make_diagnostic("RIS003", ctx, "Raises entry has no description.", target=type_token or cst_node)
