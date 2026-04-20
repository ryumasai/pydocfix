"""Rule PRM102 - Parameter has no type in docstring or signature."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.prm.helpers import bare_name, get_annotation_map, get_param_name_token, get_signature_params


@rule("PRM102", targets=FunctionCtx, cst_types=(GoogleArg, NumPyParameter))
def prm102(node: GoogleArg | NumPyParameter, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Parameter has no type annotation in either docstring or signature."""
    cst_node = node

    if isinstance(cst_node, GoogleArg):
        name_token = get_param_name_token(cst_node)
        type_token = cst_node.type
    else:
        name_token = get_param_name_token(cst_node)
        type_token = cst_node.type
    if name_token is None:
        return

    if type_token is not None and type_token.text.strip():
        return  # has type in docstring

    b = bare_name(name_token.text)
    sig_params = {bare_name(n) for n, _ in get_signature_params(ctx.parent)}
    if b not in sig_params:
        return  # not a real parameter — PRM002's responsibility
    ann_map = get_annotation_map(ctx.parent)
    if b in ann_map:
        return  # has type in signature

    message = f"Parameter '{name_token.text}' has no type in docstring or signature."
    yield make_diagnostic("PRM102", ctx, message, target=name_token)
