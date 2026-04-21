"""Rule PRM005 - Docstring has parameter not in function signature."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.helpers import delete_entry_fix
from pydocfix.rules.prm.helpers import bare_name, get_param_name_token


def _get_signature_names(func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Return bare parameter names from the function signature (includes self/cls)."""
    names: set[str] = set()
    for arg in (*func.args.posonlyargs, *func.args.args, *func.args.kwonlyargs):
        names.add(arg.arg)
    if func.args.vararg:
        names.add(func.args.vararg.arg)
    if func.args.kwarg:
        names.add(func.args.kwarg.arg)
    return names


@rule("PRM005", ctx_types=frozenset({FunctionCtx}), cst_types=frozenset({GoogleArg, NumPyParameter}))
def prm005(node: GoogleArg | NumPyParameter, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Docstring documents a parameter that does not exist in the function signature."""
    cst_node = node

    name_token = get_param_name_token(cst_node)
    if name_token is None:
        return

    sig_names = _get_signature_names(ctx.parent)
    b = bare_name(name_token.text)
    if b in sig_names:
        return

    fix = delete_entry_fix(ctx.docstring_text, cst_node.range, Applicability.UNSAFE)
    message = f"Parameter '{name_token.text}' not in function signature."
    yield make_diagnostic("PRM005", ctx, message, fix=fix, target=name_token)
