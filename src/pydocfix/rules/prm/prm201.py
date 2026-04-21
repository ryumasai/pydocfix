"""Rule PRM201 - Parameter with default value missing ``optional`` in docstring."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.diagnostics import Applicability, Diagnostic, Edit, Fix
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.prm.helpers import bare_name, get_param_name_token


def _get_default_params(func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Return bare names of parameters that have default values."""
    names: set[str] = set()
    n_args = len(func.args.args)
    n_defaults = len(func.args.defaults)
    for i, arg in enumerate(func.args.args):
        if i >= n_args - n_defaults:
            names.add(arg.arg)
    for arg, default in zip(func.args.kwonlyargs, func.args.kw_defaults, strict=False):
        if default is not None:
            names.add(arg.arg)
    return names


@rule("PRM201", ctx_types=frozenset({FunctionCtx}), cst_types=frozenset({GoogleArg, NumPyParameter}))
def prm201(node: GoogleArg | NumPyParameter, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Parameter has a default value but docstring does not mention ``optional``."""
    cst_node = node

    if isinstance(cst_node, GoogleArg):
        name_token = get_param_name_token(cst_node)
        type_token = cst_node.type
        optional_token = cst_node.optional
    else:
        name_token = get_param_name_token(cst_node)
        type_token = cst_node.type
        optional_token = cst_node.optional
    if name_token is None:
        return

    b = bare_name(name_token.text)
    default_params = _get_default_params(ctx.parent)
    if b not in default_params:
        return

    if optional_token is not None:
        return

    # Only fire if a type is already documented
    if type_token is None and not (isinstance(cst_node, GoogleArg) and cst_node.open_bracket is not None):
        return

    # Build fix
    fix = None
    if isinstance(cst_node, GoogleArg):
        if cst_node.close_bracket:
            cb_start = cst_node.close_bracket.range.start
            fix = Fix(
                edits=[Edit(start=cb_start, end=cb_start, new_text=", optional")],
                applicability=Applicability.UNSAFE,
            )
        elif type_token:
            fix = Fix(
                edits=[Edit(start=type_token.range.end, end=type_token.range.end, new_text=", optional")],
                applicability=Applicability.UNSAFE,
            )
    else:  # NumPyParameter
        if type_token:
            fix = Fix(
                edits=[Edit(start=type_token.range.end, end=type_token.range.end, new_text=", optional")],
                applicability=Applicability.UNSAFE,
            )

    message = f"Parameter '{name_token.text}' has default value but docstring does not mention 'optional'."
    yield make_diagnostic("PRM201", ctx, message, fix=fix, target=name_token)
