"""Rule PRM102 - Parameter has no type in docstring or signature."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic
from pydocfix.rules.prm._helpers import bare_name, get_annotation_map, get_param_name_token, get_signature_params


class PRM102(BaseRule[GoogleArg | NumPyParameter]):
    """Parameter has no type annotation in either docstring or signature."""

    code = "PRM102"

    def diagnose(self, node: GoogleArg | NumPyParameter, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

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
        sig_params = {bare_name(n) for n, _ in get_signature_params(ctx.parent_ast)}
        if b not in sig_params:
            return  # not a real parameter — PRM002's responsibility
        ann_map = get_annotation_map(ctx.parent_ast)
        if b in ann_map:
            return  # has type in signature

        message = f"Parameter '{name_token.text}' has no type in docstring or signature."
        yield self._make_diagnostic(ctx, message, target=name_token)
