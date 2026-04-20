"""Rule PRM003 - Docstring documents ``self`` or ``cls``."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.helpers import delete_entry_fix
from pydocfix.rules.prm.helpers import get_param_name_token


@rule("PRM003", targets=FunctionCtx, cst_types=(GoogleArg, NumPyParameter))
def prm003(node: GoogleArg | NumPyParameter, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Docstring should not document ``self`` or ``cls``."""
    cst_node = node

    name_token = get_param_name_token(cst_node)
    if name_token is None:
        return

    if name_token.text not in ("self", "cls"):
        return

    fix = delete_entry_fix(ctx.docstring_text, cst_node.range, Applicability.SAFE)
    message = f"Docstring should not document '{name_token.text}'."
    yield make_diagnostic("PRM003", ctx, message, fix=fix, target=name_token)
