"""Rule PRM008 - Docstring parameter has empty description."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.prm.helpers import get_param_name_token


@rule("PRM008", ctx_types=frozenset({FunctionCtx}), cst_types=frozenset({GoogleArg, NumPyParameter}))
def prm008(node: GoogleArg | NumPyParameter, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Docstring parameter has no description."""
    cst_node = node

    name_token = get_param_name_token(cst_node)
    if name_token is None:
        return

    desc = cst_node.description
    if desc is not None and desc.text.strip():
        return

    message = f"Parameter '{name_token.text}' has no description."
    yield make_diagnostic("PRM008", ctx, message, target=name_token)
