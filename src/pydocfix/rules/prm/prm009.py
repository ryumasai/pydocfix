"""Rule PRM009 - Docstring parameter name missing '*' or '**' prefix."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.diagnostics import Applicability, Diagnostic, Fix
from pydocfix.fixes import replace_token
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.prm.helpers import get_param_name_token


def _get_vararg_kwarg_names(func: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, str]:
    """Return mapping of bare name -> prefixed name for *args/**kwargs."""
    result: dict[str, str] = {}
    if func.args.vararg:
        result[func.args.vararg.arg] = f"*{func.args.vararg.arg}"
    if func.args.kwarg:
        result[func.args.kwarg.arg] = f"**{func.args.kwarg.arg}"
    return result


@rule("PRM009", targets=FunctionCtx, cst_types=(GoogleArg, NumPyParameter))
def prm009(node: GoogleArg | NumPyParameter, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Docstring parameter name missing '*' or '**' prefix."""
    cst_node = node

    name_token = get_param_name_token(cst_node)
    if name_token is None:
        return

    param_name = name_token.text
    if param_name.startswith("*"):
        return

    prefixed_names = _get_vararg_kwarg_names(ctx.parent)
    expected = prefixed_names.get(param_name)
    if expected is None:
        return

    fix = Fix(
        edits=[replace_token(name_token, expected)],
        applicability=Applicability.SAFE,
    )
    message = f"Docstring parameter '{param_name}' should be '{expected}'."
    yield make_diagnostic("PRM009", ctx, message, fix=fix, target=name_token)
